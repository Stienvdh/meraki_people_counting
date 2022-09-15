from flask import Flask 
import requests 
import json 
import time
import datetime
import pytz
import paho.mqtt.client as mqtt
from env_var import CAMERA_SERIAL, MQTT_SERVER, MQTT_PORT, MERAKI_API_KEY


app = Flask(__name__)

global display 
display=[0,0,800] 
obj_tracker = {}
MQTT_TOPIC = "/merakimv/" + CAMERA_SERIAL + "/raw_detections" 

local_timezone = pytz.timezone("Europe/Berlin")

def current_milli_time():
    return round(time.time() * 1000) 


#Getting the zones defined in the Meraki dashboard
def getMVZones(serial_number):
    url = "https://api.meraki.com/api/v0/devices/"+serial_number+"/camera/analytics/zones"

    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        "Content-Type": "application/json"
    }

    resp = requests.request("GET", url, headers=headers)
    zones = resp.json()

    for zone in zones:
        if zone["label"] == "door1":
            door1ZoneCoords = zone["regionOfInterest"]
        
        if zone["label"] == "door2":
             door2ZoneCoords = zone["regionOfInterest"]
    
    if int(resp.status_code / 100) == 2:
        
        return(door1ZoneCoords,door2ZoneCoords)  
    return('link error')


def on_connect(client, userdata, flags, rc):
    print("connected with code: " + str(rc))
    print(datetime.datetime.now(local_timezone).time())
    client.subscribe(MQTT_TOPIC)
    global zones
    zones = getMVZones(CAMERA_SERIAL)
   

def on_message(client, userdata, msg):
    global obj_tracker
    global payload
   
    

    payload = json.loads(msg.payload.decode("utf-8", "ignore"))

    door1ZoneCoords = zones[0] 
    door2ZoneCoords = zones[1] 

    ts = payload["ts"]
    ts_in_datetime = datetime.datetime.fromtimestamp(ts/1000).strftime('%Y-%m-%d %H:%M:%S')

    global objects
    objects = payload["objects"]
    oid_keys = []
      


    for obj in objects: 
        #Store objects current coordinates
        coordx0 = obj['x0']
        coordx1 = obj['x1']
        coordy0 = obj['y0']
        coordy1 = obj['y1']

        # Store object id in oid
        oid = obj["oid"]
        
        # Add oid to oid_keys
        oid_keys.append(oid)


        # If it is a new object, then add object to obj_tracker, and set variables
        if oid not in obj_tracker:

            obj_to_add = {}
            obj_to_add["ts_start"] = ts
            obj_to_add["age"] = current_milli_time() - ts
            obj_to_add["new_object"] = True
                
            #saving objects coordinates :
            obj_to_add["coordx0"] = coordx0
            obj_to_add["coordx1"] = coordx1
            obj_to_add["coordy0"] = coordy0
            obj_to_add["coordy1"] = coordy1       

            obj_to_add["indoor1Area"] = False
            obj_to_add["initialdoor1Coord"] = 0
            obj_to_add["exiting"] = None #True/False value. If going exiting direction, then True. If going entering direction, the False. 
            obj_to_add["directionCounted"] = False #If an object's direction has already been counted, then it is set to True 
            obj_to_add["yCoordDiff"] = 0 



            obj_to_add["indoor2Area"] = False
            obj_to_add["initialdoor2AreaCoord"] = 0
            obj_to_add["directionCounted"] = False #If an object's direction has already been counted, then it is set to True 
            obj_to_add["yCoordDifft2"] = 0 

            obj_tracker[oid] = obj_to_add

            # If the object is already present in obj_tracker, then update the object age, set new_object to False
        else: 
            obj_tracker[oid]["age"] = current_milli_time() - obj_tracker[oid]["ts_start"]
            obj_tracker[oid]["new_object"] = False
            


        if float(door1ZoneCoords["x0"]) <= coordx0 <= float(door1ZoneCoords["x1"]) and float(door1ZoneCoords["y0"]) <= coordy0 <= float(door1ZoneCoords["y1"]):
        
           
            #If object is inside the Doorway area for the first time, record the y0 coordinate that object had when entering the area, and set inDoorwayArea to True
            if obj_tracker[oid]["indoor1Area"] == False:
                obj_tracker[oid]["initialdoor1Coord"] = coordy0
                obj_tracker[oid]["indoor1Area"] = True
                
           
            #If object previously was in Doorway area, record the difference in object's y0 coordinate since object entered the area   
            else:
                obj_tracker[oid]["yCoordDiff"] = obj_tracker[oid]["initialdoor1Coord"] - coordy0
                
                #If object is exiting, y0 should have decreased. If the y0 coordinate has changed with more than 0.1, object has likely exited through door. Increment exitingDirectionCounter.
                if obj_tracker[oid]["yCoordDiff"] > 0 and abs(obj_tracker[oid]["yCoordDiff"]) >= 0.1 and obj_tracker[oid]["directionCounted"] == False:
                    obj_tracker[oid]["exiting"] = True 
                    obj_tracker[oid]["indoor1Area"] = True 
                    print("\nobject is in exiting direction door 1")
                    obj_tracker[oid]["directionCounted"] = True
                    display[0]+=1
                    display[2]-=1
                    if display[2]== 790 and display[1]==0:
                         display[1]+= 10
                    elif display[1] !=0:
                         display[1]+=1
  
                    print("ts: ", ts_in_datetime)
                    # print(current_milli_time())
                    print("yCoordDiff: ", obj_tracker[oid]["yCoordDiff"])
                    print("The person in the doorway area has oid: ",oid)
                    print("-----------------")
                    if display[1] !=0:
                        print(display[0] , "-----" , display[1] , "-----" , display[2])
                    else:
                        print(display[0] , "-----" , "-" , "-----" , display[2])
                    print("-----------------")
                    

                #If object is entering, y0 should have increased. If the y0 coordinate has changed with more than 0.1, object has likely entered through door. Increment enteringDirectionCounter.
                if obj_tracker[oid]["yCoordDiff"] < 0 and abs(obj_tracker[oid]["yCoordDiff"]) >= 0.1  and obj_tracker[oid]["directionCounted"] == False: 
       
                    obj_tracker[oid]["exiting"] = False
                    obj_tracker[oid]["directionCounted"] = True
                    obj_tracker[oid]["indoor1Area"] = True 
                    print("\nobject is in entering direction door 1")
                    if display[1] != 0:
                        display[1]-=1
                    if display[2]<800:    
                        display[2]+=1
                    print("ts: ", ts_in_datetime)
                    # print(current_milli_time())
                    print("yCoordDiff: ", obj_tracker[oid]["yCoordDiff"])
                    print("The person in the doorway area has oid: ",oid)
                    print("-----------------")
                    if display[1] != 0:
                        print(display[0] , "-----" , display[1] , "-----" , display[2])
                    else:
                        print(display[0] , "-----" , "-" , "-----" , display[2])
                    print("-----------------")

        
        
        elif float(door2ZoneCoords["x0"]) <= coordx0 <= float(door2ZoneCoords["x1"]) and float(door2ZoneCoords["y0"]) <= coordy0 <= float(door2ZoneCoords["y1"]) and obj_tracker[oid]["indoor1Area"]== False:
            
           
            #If object is inside the Doorway area for the first time, record the y0 coordinate that object had when entering the area, and set inDoorwayArea to True
            if obj_tracker[oid]["indoor2Area"] == False:
                obj_tracker[oid]["initialdoor2AreaCoord"] = coordy0
                obj_tracker[oid]["indoor2Area"] = True
                
           
            #If object previously was in Doorway area, record the difference in object's y0 coordinate since object entered the area   
            else:
                obj_tracker[oid]["yCoordDifft2"] = obj_tracker[oid]["initialdoor2AreaCoord"] - coordy0
                
                #If object is exiting, y0 should have decreased. If the y0 coordinate has changed with more than 0.1, object has likely exited through door. Increment exitingDirectionCounter.
                if obj_tracker[oid]["yCoordDifft2"] > 0 and abs(obj_tracker[oid]["yCoordDifft2"]) >= 0.1 and obj_tracker[oid]["directionCounted"] == False and obj_tracker[oid]["indoor1Area"]== False:
                    
                    obj_tracker[oid]["exiting"] = True 
                    print("\nobject is in exiting direction door 2")
                    obj_tracker[oid]["directionCounted"] = True
                    display[0]+=1
                    display[2]-=1
                    if display[2]== 790 and display[1]==0:
                         display[1]+=10
                    elif display[1] !=0:
                         display[1]+=1

  
                    print("ts: ", ts_in_datetime)
                    # print(current_milli_time())
                    print("yCoordDiff: ", obj_tracker[oid]["yCoordDiff"])
                    print("The person in the doorway area has oid: ",oid)
                    print("-----------------")
                    if display[1] != 0:
                        print(display[0] , "-----" , display[1] , "-----" , display[2])
                    else:
                        print(display[0] , "-----" , "-" , "-----" , display[2])
                    print("-----------------")
                    

                #If object is entering, y0 should have increased. If the y0 coordinate has changed with more than 0.1, object has likely entered through door. Increment enteringDirectionCounter.
                if obj_tracker[oid]["yCoordDifft2"] < 0 and abs(obj_tracker[oid]["yCoordDifft2"]) >= 0.1  and obj_tracker[oid]["directionCounted"] == False and obj_tracker[oid]["indoor1Area"]== False: 
       
                    obj_tracker[oid]["exiting"] = False
                    obj_tracker[oid]["directionCounted"] = True

                    print("\nobject is in entering direction door 2")
                    if  display[1] != 0:
                        display[1]-=1
                    if display[2]<800:    
                        display[2]+=1
                    print("ts: ", ts_in_datetime)
                    #print(current_milli_time())
                    print("yCoordDiff: ", obj_tracker[oid]["yCoordDiff"])
                    print("The person in the doorway area has oid: ",oid)
                    print("-----------------")
                    if display[1] != 0:
                        print(display[0] , "-----" , display[1] , "-----" , display[2])
                    else:
                        print(display[0] , "-----" , "-" , "-----" , display[2])
                    print("-----------------")

            
                #If object is not in the Doorway area, reset 'inDoorwayArea', 'directionCounted' and 'exiting' variables
        else:

            obj_tracker[oid]["indoor1Area"] = False
            obj_tracker[oid]["indoor2Area"] = False
            obj_tracker[oid]["directionCounted"] = False
            obj_tracker[oid]["exiting"] = None

        

     

    obj_tracker_temp = {}
    for key in oid_keys:
        obj_tracker_temp[key] = obj_tracker[key]

    #Update the coordinates for each object
    for key in obj_tracker:
        if key in obj_tracker_temp:

            obj_tracker_temp[key]["coordx0"] = coordx0
            obj_tracker_temp[key]["coordy0"] = coordy0
            obj_tracker_temp[key]["coordx1"] = coordx1
            obj_tracker_temp[key]["coordy1"] = coordy1
                  
    obj_tracker.clear()
    obj_tracker = obj_tracker_temp




if __name__ == "__main__":

    try:
        
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(MQTT_SERVER, MQTT_PORT, 60)
        client.loop_start() 
        app.run(host='0.0.0.0', port=5001) 

    except Exception as ex:
        print("[MQTT]failed to connect or receive msg from mqtt, due to: \n {0}".format(ex))


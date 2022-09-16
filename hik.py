

from hcnetsdk import HCNetSDK, NET_DVR_DEVICEINFO_V30, NET_DVR_DEVICEINFO_V30, NET_DVR_SETUPALARM_PARAM, \
    fMessageCallBack, COMM_ALARM_V30, COMM_ALARM_VIDEO_INTERCOM, NET_DVR_VIDEO_INTERCOM_ALARM, NET_DVR_ALARMINFO_V30, \
    ALARMINFO_V30_ALARMTYPE_MOTION_DETECTION, VIDEO_INTERCOM_ALARM_ALARMTYPE_DOORBELL_RINGING, \
    VIDEO_INTERCOM_ALARM_ALARMTYPE_DISMISS_INCOMING_CALL, VIDEO_INTERCOM_ALARM_ALARMTYPE_TAMPERING_ALARM, \
    VIDEO_INTERCOM_ALARM_ALARMTYPE_DOOR_NOT_CLOSED, COMM_UPLOAD_VIDEO_INTERCOM_EVENT, NET_DVR_VIDEO_INTERCOM_EVENT, \
    VIDEO_INTERCOM_EVENT_EVENTTYPE_UNLOCK_LOG, VIDEO_INTERCOM_EVENT_EVENTTYPE_ILLEGAL_CARD_SWIPING_EVENT, \
    NET_DVR_UNLOCK_RECORD_INFO
from ctypes import POINTER, cast, c_char_p, c_byte
import config
import paho.mqtt.client as mqtt


def callback(command: int, alarmer_pointer, alarminfo_pointer, buffer_length, user_pointer):
    if (command == COMM_ALARM_V30):
        alarminfo_alarm_v30: NET_DVR_ALARMINFO_V30 = cast(
            alarminfo_pointer, POINTER(NET_DVR_ALARMINFO_V30)).contents
        if (alarminfo_alarm_v30.dwAlarmType == ALARMINFO_V30_ALARMTYPE_MOTION_DETECTION):
            print(f"Motion detected")
            client.publish(config.mqtt_topic + "/motion")
        else:
            print(
                f"COMM_ALARM_V30, unhandled dwAlarmType: {alarminfo_alarm_v30.dwAlarmType}")
    elif (command == COMM_ALARM_VIDEO_INTERCOM):
        alarminfo_alarm_video_intercom: NET_DVR_VIDEO_INTERCOM_ALARM = cast(
            alarminfo_pointer, POINTER(NET_DVR_VIDEO_INTERCOM_ALARM)).contents
        if (alarminfo_alarm_video_intercom.byAlarmType == VIDEO_INTERCOM_ALARM_ALARMTYPE_DOORBELL_RINGING):
            print("Doorbell ringing")
            client.publish(config.mqtt_topic + "/ringing")
        elif (alarminfo_alarm_video_intercom.byAlarmType == VIDEO_INTERCOM_ALARM_ALARMTYPE_DISMISS_INCOMING_CALL):
            print("Call dismissed")
            client.publish(config.mqtt_topic + "/dismissed")
        elif (alarminfo_alarm_video_intercom.byAlarmType == VIDEO_INTERCOM_ALARM_ALARMTYPE_TAMPERING_ALARM):
            print("Tampering alarm")
            client.publish(config.mqtt_topic + "/tamper")
        elif (alarminfo_alarm_video_intercom.byAlarmType == VIDEO_INTERCOM_ALARM_ALARMTYPE_DOOR_NOT_CLOSED):
            print("Door not closed")
            client.publish(config.mqtt_topic + "/notclosed")
        else:
            print(
                f"COMM_ALARM_VIDEO_INTERCOM, unhandled byAlarmType: {alarminfo_alarm_video_intercom.byAlarmType}")
    elif (command == COMM_UPLOAD_VIDEO_INTERCOM_EVENT):
        alarminfo_upload_video_intercom_event: NET_DVR_VIDEO_INTERCOM_EVENT = cast(
            alarminfo_pointer, POINTER(NET_DVR_VIDEO_INTERCOM_EVENT)).contents
        if (alarminfo_upload_video_intercom_event.byEventType == VIDEO_INTERCOM_EVENT_EVENTTYPE_UNLOCK_LOG):
            print(
                f"Unlocked by: {list(alarminfo_upload_video_intercom_event.uEventInfo.struUnlockRecord.byControlSrc)}")
            card_id = bytes(alarminfo_upload_video_intercom_event.uEventInfo.struUnlockRecord.byControlSrc).hex()
            client.publish(config.mqtt_topic + "/unlocked", card_id)

        elif (
                alarminfo_upload_video_intercom_event.byEventType == VIDEO_INTERCOM_EVENT_EVENTTYPE_ILLEGAL_CARD_SWIPING_EVENT):
            print(f"Illegal card swiping")
            client.publish(config.mqtt_topic + "/illegalcard")
        else:
            print(
                f"COMM_ALARM_VIDEO_INTERCOM, unhandled byEventType: {alarminfo_upload_video_intercom_event.byEventType}")
    else:
        print(f"Unhandled command: {command}")

print("Connecting camera...")

HCNetSDK.NET_DVR_Init()
HCNetSDK.NET_DVR_SetValidIP(0, True)

# device_info = NET_DVR_DEVICEINFO_V30()
user_id = HCNetSDK.NET_DVR_Login_V30(config.intercom_host.encode('utf-8'), 8000, config.intercom_user.encode('utf-8'),
                                     config.intercom_pass.encode('utf-8'))

if (user_id < 0):
    print(
        f"NET_DVR_Login_V30 failed, error code = {HCNetSDK.NET_DVR_GetLastError()}")
    HCNetSDK.NET_DVR_Cleanup()
    exit(1)

print ("Connected!")

alarm_param = NET_DVR_SETUPALARM_PARAM()
alarm_param.dwSize = 20
alarm_param.byLevel = 1
alarm_param.byAlarmInfoType = 1
alarm_param.byFaceAlarmDetection = 1

alarm_handle = HCNetSDK.NET_DVR_SetupAlarmChan_V41(user_id, alarm_param)

if (alarm_handle < 0):
    print(
        f"NET_DVR_SetupAlarmChan_V41 failed, error code = {HCNetSDK.NET_DVR_GetLastError()}")
    HCNetSDK.NET_DVR_Logout_V30(user_id)
    HCNetSDK.NET_DVR_Cleanup()
    exit(2)

message_callback = fMessageCallBack(callback)
HCNetSDK.NET_DVR_SetDVRMessageCallBack_V50(0, message_callback, user_id)


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("MQTT connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe("$SYS/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))


print("Connecting mqtt...")
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
if (config.mqtt_user != ""):
    client.username_pw_set(config.mqtt_user, config.mqtt_pass)
client.connect(config.mqtt_host, 1883, 60)

client.loop_forever()
print("Done")

# never called anyway..
# HCNetSDK.NET_DVR_CloseAlarmChan_V30(alarm_handle)
# HCNetSDK.NET_DVR_Logout_V30(user_id)
# HCNetSDK.NET_DVR_Cleanup()

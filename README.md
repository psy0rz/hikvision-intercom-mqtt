# Hikvision intercom to MQTT bridge.

This will connect to your intercom and send events to mqtt.

Probably works with all Hikvision video intercoms, like: 
 * DS-KD8003
 * DS-KV8113
 * DS-KV8213
 * DS-KV6113
 * DS-KV8413

Since it uses the official SDK it doesnt require custom firmware or other special things.

Edit config.py and run hik.py and see what happens. :)

It send events when someone is ringing, where there is motion, or when the unlock-button is pressed via the app. (and a few others like tamper alarm)

**NOTE: hikvision actually queues the events, so the first time you will get a whole list of events, in a slow manner. just wait until its done**

# Install

Edit docker-compose.yml and use:
```shell
docker-compose up
```


## Other info

TODO: add opening door via mqtt as well. (i dont need it myself yet)

Based off the excellent example from: https://github.com/laszlojakab/hikvision-intercom-python-demo



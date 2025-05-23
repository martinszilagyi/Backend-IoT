# Beam Buddy : IoT-Enabled Smart Bike Light

### **Group 1**: Dahlia Dry (s250127), Emil Noerspang (s225277), Simon Schütz (s250681), Andreas Svartá (s204185), Martin Szilágyi (s243162), Ran Wang (s111503)

### Description
This repository contains the code for a Flask web app which serves as the graphical user interface for our IoT-enabled smart bike light. The app fetches updates from the bike light via a webhook to The Things Network (TTN), and uses wifi node data to perform geolocation by querying a Google API. The app is currently deployed on Railway here: https://iot-production-390a.up.railway.app/. 

### Abstract

Bike lights are a critical safety component for any cyclist, but they are often unreliable (run out of battery), easily stolen, or easy to forget. In this report, we present a solution to these problems in the form of an IoT-enabled smart bike light. The bike light consists of both a front and rear light using a Heltec HT-CT62 as the MCU, with LoRaWAN connectivity via The Things Network enabling a web-based user interface which displays geolocation, battery level, and operational status. It turns on automatically with movement and functions additionally as a theft alarm by using an RFID card to lock/unlock the device when parked. It also features solar charging and is designed with a focus on maximizing battery life, with an audible warning for low battery included. All of these features combine to make both the user and their bike safer, day and night.

![Beam Buddy Poster](https://github.com/martinszilagyi/Backend-IoT/blob/main/static/img/34346-poster.png)

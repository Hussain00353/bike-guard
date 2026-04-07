BikeGuard - IoT Bike Theft Detection System
============================================
Author: Hussain00353
GitHub: https://github.com/Hussain00353/bike-guard
Live Dashboard: http://bike-guard-env.eba-7ei3v36y.us-east-1.elasticbeanstalk.com

OVERVIEW
--------
BikeGuard is a real-time IoT bike theft detection system built for the
Fog and Edge Computing module. It uses 5 mock sensors, a virtual fog node,
and a fully scalable AWS cloud backend to detect and alert bike theft in
real time.

REQUIREMENTS
------------
- Python 3.8+
- AWS Academy account with access to:
  * AWS IoT Core
  * AWS SQS
  * AWS Lambda
  * AWS DynamoDB
  * AWS API Gateway (REST)
  * AWS Elastic Beanstalk

INSTALLATION
------------
1. Clone the repository:
   git clone https://github.com/Hussain00353/bike-guard.git
   cd bike-guard

2. Create and activate virtual environment:
   python3 -m venv venv
   source venv/bin/activate  (Mac/Linux)
   venv\Scripts\activate     (Windows)

3. Install required packages:
   pip install -r requirements.txt

4. Add your AWS certificates to certs/ folder:
   - xxxx-certificate.pem.crt
   - xxxx-private.pem.key
   - AmazonRootCA1.pem

5. Create .env file in root folder:
   AWS_ENDPOINT=your-endpoint.iot.us-east-1.amazonaws.com
   CERT_PATH=certs/your-certificate.pem.crt
   KEY_PATH=certs/your-private-key.pem.key
   CA_PATH=certs/AmazonRootCA1.pem
   VIBRATION_INTERVAL=5
   GPS_INTERVAL=10
   TILT_INTERVAL=5
   SOUND_INTERVAL=5
   BATTERY_INTERVAL=30

AWS SETUP
---------
1. AWS IoT Core:
   - Create Thing: bike-guard-001
   - Create Policy: BikeGuardPolicy (allow connect, publish, subscribe, receive)
   - Attach policy to certificate

2. AWS SQS:
   - Create Standard Queue: bike-guard-queue

3. AWS DynamoDB:
   - Create Table: bike-guard-data
   - Partition key: deviceId (String)
   - Sort key: timestamp (String)

4. AWS Lambda - bike-guard-processor:
   - Runtime: Python 3.12
   - Role: LabRole
   - Trigger: SQS (bike-guard-queue)
   - Code: backend/lambda_processor.py

5. AWS Lambda - bike-guard-api:
   - Runtime: Python 3.12
   - Role: LabRole
   - Code: backend/lambda_api.py

6. AWS API Gateway (REST):
   - Create REST API: bike-guard-rest-api
   - Resource: /data
   - Method: GET → bike-guard-api Lambda
   - Enable CORS
   - Deploy to stage: prod

7. AWS IoT Rule:
   - Name: bike_guard_to_sqs
   - SQL: SELECT * FROM 'bike/fog/processed'
   - Action: Forward to bike-guard-queue SQS

8. AWS Elastic Beanstalk:
   - Create Application: bike-guard
   - Platform: Python 3.14 on Amazon Linux 2023
   - Upload: bike-guard-app.zip
   - Role: LabRole / LabInstanceProfile

RUNNING THE PROJECT
-------------------
Start everything with one command:
   cd bike-guard
   ./start.sh

This starts:
- All 5 mock sensors
- Fog node
- Local Flask server (for development)

DASHBOARD
---------
Live (Elastic Beanstalk):
http://bike-guard-env.eba-7ei3v36y.us-east-1.elasticbeanstalk.com

Local development:
http://localhost:8080

PROJECT STRUCTURE
-----------------
bike-guard/
├── sensors/                - 5 mock IoT sensors
│   ├── vibration_sensor.py - Detects shaking (0-8G)
│   ├── gps_sensor.py       - Tracks location (Dublin)
│   ├── tilt_sensor.py      - Detects lifting (0-90°)
│   ├── sound_sensor.py     - Detects alarm (0-120dB)
│   └── battery_sensor.py   - Monitors power level
├── fog/
│   └── fog_node.py         - Local theft detection brain
├── backend/
│   ├── lambda_processor.py - SQS → DynamoDB processor
│   └── lambda_api.py       - REST API → Dashboard
├── dashboard/
│   ├── index.html          - Dashboard HTML
│   ├── style.css           - Dashboard styles
│   └── app.js              - Dashboard JavaScript
├── .ebextensions/
│   └── python.config       - Elastic Beanstalk config
├── application.py          - Flask web app (EB entry point)
├── start.sh                - One-command startup script
├── requirements.txt        - Python dependencies
└── readme.txt              - This file

SENSORS EXPLAINED
-----------------
Sensor          Normal Range    Alert Range     Interval
Vibration       0.0 - 1.5 G    2.0 - 8.0 G    5 seconds
GPS             Parked          Moving          10 seconds
Tilt            15 - 20 deg    45 - 90 deg     5 seconds
Sound           30 - 50 dB     80 - 120 dB     5 seconds
Battery         50 - 100 %     0 - 20 %        30 seconds

THEFT DETECTION LOGIC
---------------------
The fog node monitors all 5 sensors simultaneously.
If 2 or more sensors trigger an alert at the same time,
a THEFT DETECTED event is generated and dispatched to AWS.

REUSE CITATION
--------------
The MQTT connection pattern in the sensor files and fog node
is based on the lab exercise provided in the Fog and Edge
Computing module (Lab_MQTT tutorial, AWS IoT Core Python SDK).
The original lab code has been extended and adapted for this
project's bike theft detection use case.
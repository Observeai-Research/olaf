<div id="top"></div>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/Observeai-Research/olaf">
    <img src="images/logo.png" alt="🤖" width="80" height="80">
  </a>

  <h3 align="center">One-Load-Auditor-Framework</h3>

  <p align="center">
    An easy to use load generation and testing framework for anyone.
    <br />
    <a href="https://github.com/Observeai-Research/olaf/issues">Report Bug</a>
    ·
    <a href="https://github.com/Observeai-Research/olaf/issues">Request Feature</a>
  </p>
</div>




<!-- ABOUT THE PROJECT -->
## About The Project

Olaf is simple GUI based tool to orchestrate load testing and load generation.
It uses Streamlit as its front end, and Locust as its backend.

Here's why you should use Olaf:
* Easy to set-up and use, load test with click of a button.
* Support for multiple resources out of the box
* Auto backup of all the load test results for tracking load results over time.

![Product Name Screen Shot][product-screenshot]




<p align="right">(<a href="#top">back to top</a>)</p>



### Built With ❤️
* [streamlit](https://github.com/streamlit/streamlit)
* [locust](https://github.com/locustio/locust)
* [pydantic](https://github.com/samuelcolvin/pydantic)
* [boto3](https://github.com/boto/boto3)
* [sagemaker-python-sdk](https://github.com/aws/sagemaker-python-sdk)
* [elasticsearch-py](https://github.com/elastic/elasticsearch-py)
* [mongo-python-driver](https://github.com/mongodb/mongo-python-driver)
* [tinydb](https://github.com/msiemens/tinydb)

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started With Docker

Olaf is completely containerized with docker, which also the preferred way of getting started.

To install docker for your machine, refer [link](https://docs.docker.com/engine/install/)

To get a local copy up and running is just one simple command:

```shell
 docker build -t olaf . 
 docker run -p 80:8000 olaf
```

The Olaf dashboard can be accessed using following url with creds `olaf / olaf`
```shell
http://localhost
```

## Getting Started Without Docker
### Prerequisites

The project is developed and tested with python3.8.
Make sure a compatible version is installed.

* install poetry from https://python-poetry.org/

* cd to root folder of the project.
* create a virtual environment 
  ```shell
    virtualenv -p python3.8 venv
    source venv/bin/activate
    ```
* install dependencies
  ```sh
  poetry install
  ```

### Running Olaf

After installing relevant dependencies, Olaf can be run using:
```shell
PYTHONPATH=./ streamlit run src/streamlit_app/app.py --browser.gatherUsageStats false
```
The Olaf dashboard can be accessed using following url
```shell
http://localhost:8501
```
The Locust dashboard can be accessed at;
```shell
http://localhost:12311/
```

<p align="right">(<a href="#top">back to top</a>)</p>


## Olaf Usage

Olaf is a super simple to get started using following steps:
1. Once on Olaf is up and running, you will land on Olaf Dashboard.
2. Chose the resource to load test from the sidebar.
3. Fill out the parameters required to do the load test.
4. Click on `START LOAD SESSION`.
5. A link will be generated, navigate to the link.
6. You will be presented with a locust dashboard. to do the load test.
7. Once done, simply click on `STOP LOAD SESSION` from  Olaf Dashboard.

## Advanced Olaf Usage
You can improve your productivity with following advanced options:
1. Automate Run: The option is supported for every kind of resource. 
   This allows you to automatically run the load test for fixed duration directly from the Olaf dashboard.
   Simply click on Automate Run and configure the following parameters:
   1. `test duration in seconds`: duration for which test is to be run. 
      You can navigate to locust dashboard while test is running.
   2. `autoquit timeout after completion`: time after which to end load session after load test is complete. 
      You will not be able to navigate to locust dashboard, after load session is ended.
   3. `users to spawn`: the number of concurrent users to spawn.
   4. `spawn rate`: the rate at which users to spawn per second.
2. Olaf Schedule (Beta): Olaf schedules are used to generate load in particular shape. 
   This is achieved using a configuration in form of a list. 
   Every element in the list is a JSON configuration specifying the load configuration for a particular duration.
   For example, to generate load of following description:
   1. For first 300 seconds, generate load at 2 RPS per user with total of 3 users.
   2. For the next 30 seconds, generate load at 3 RPS per user with total of 1 user.
   We can use the following configuration:
   ```json
            [
             {"duration": 300, "users": 3, "spawn_rate": 3, "rps": 2},
             {"duration": 30,  "users": 1, "spawn_rate": 1, "rps": 3}
            ]
   ```
   Olaf schedule is only supported for SQS and SNS resource types.
   
3. Automated Backup of Load Test Report: Olaf supports automatically backing of load test results 
   (locust reports) to s3 bucket. To enable this by configuring following fields in ```src/config/config.yaml```.
   ```yaml
   aws_config:
     key: <aws credential having access to s3 bucket>
     secret: <aws credential having access to s3 bucket>
   s3_config:
    region: <region via which to connect to aws bucket>
    bucket_name: <bucket where to store load test result>
    base_path: <path within bucket to store load test result>
   ```

## Supported Resources

Olaf gives support for load test and load generation across multiple Resources out-of-the-box.
This section describes various configuration parameters required for each of the Resources:

### REST GET
1. `URL`: Complete URL (including HTTP/HTTPS) to load the test. Any URL parameters can be included as well.
2. `Header JSON`: Headers for the request, if any. 
3. `Load Session Name`: Name of the current session.

### REST POST
1. `URL`: Complete URL (including HTTP/HTTPS) to load the test. Any URL parameters can be included as well.
2. `Header JSON`: Headers for the request, if any.
3. `List of Query JSON`: JSON body of the request. Each request needs to be one entry in the list. Alternatively this 
   can be uploaded as a text file as well.
4. `Load Session Name`: Name of the current session.

### Elasticsearch
1. `ES URL`: The endpoint of Elasticsearch URL.
2. `ES Username`: The username of the Elasticsearch instance.
3. `ES Password`: The username of the Elasticsearch instance.
4. `ES Index Name`: The index under load test.
5. `List of Query JSON`: Any ES search query. Each read query needs to be part of list. Alternatively this 
   can be uploaded as a text file as well. Internally, this uses `es.search` of  `elasticsearch-py`.
6. `Load Session Name`: Name of the current session.

### Lambda
1. `Lambda ARN`: Lambda ARN to load test.
2. `AWS region`: Region of AWS resource under test.
3. `AWS access key / AWS secret key`: AWS credentials having access to the resource under test.
4. `List of Query JSON`: JSON request to hit lambda with. Each request needs to be part of list. Alternatively this 
   can be uploaded as a text file as well.
5. `Load Session Name`: Name of the current session.

### MongoDB
1. `Mongo URL`: Mongo URL in SRV format
2. `Database`: Database to load test.
3. `Collection`: Collection within a database to load test.
4. `List of Query JSON`: Any MongoDB search query. Each search query needs to be part of list. Alternatively this 
   can be uploaded as a text file as well. 
5. `Load Session Name`: Name of the current session.

### Sagemaker
1. `Sagemaker endpoint`: Endpoint of sagemaker to test.
2. `Predictor type`: Pytorch, Sklearn and Tensorflow are the supported predictor types.
3. `Input/Output Serializer`: The serializer the model is expected to work with. 
4. `AWS region`: Region of AWS resource under test. 
5. `AWS access key / AWS secret key`: AWS credentials having access to the resource under test.
6. `List of query JSON`: Input to Sagemaker model endpoint. Each input needs to be part of list. Alternatively this 
   can be uploaded as a text file as well. If the endpoint to be tested is a multi-model endpoint, you are expected to
   pass the input as a list of dictionaries of format: 
   `{"payload": YOUR_INPUT_PAYLOAD, "target_model": MODEL_TAR_FILE_NAME}` 
7. `Batch Mode`: When enabled, a batch of size `b` is created by random sampling `b` inputs from the list of query JSON.
   Each batch is then sent as a single request.
8. `Load Session Name`: Name of the current session.

### SQS
1. `SQS Name`: Name (not arn) of the SQS queue to generate load in. 
2.` AWS region`: Region of AWS resource under test. 
3. `AWS access key / AWS secret key`: AWS credentials having access to the resource under test.
4. `List of query JSON`: Message to be sent to SQS. Each message needs to be part of list. Alternatively this 
   can be uploaded as a text file as well.
5. `message Attribute JSON`: Message Attribute to be sent with every message. We currently do not support 
   message attribute per message.
6. `Load Session Name`: Name of the current session.

### SQS
1. `SNS ARN`: ARN of the SNS topic to generate load in. 
2. `AWS region`: Region of AWS resource under test. 
3. `AWS access key / AWS secret key`: AWS credentials having access to the resource under test.
4. `List of query JSON`: Message to be sent to SNS. Each message needs to be part of list. Alternatively this 
   can be uploaded as a text file as well.
5. `message Attribute JSON`: Message Attribute to be sent with every message. We currently do not support 
   message attribute per message.
6. `Load Session Name`: Name of the current session.

### PineCone Vector Search
1. `API KEY`: API Key of the VectorDB 
2. `ENVIRONMENT NAME`: ENV name of the AWS region
3. `Index Name`: Index name of the VectorDB
4. `List of query JSON`: List of Vector Query
5. `Load Session Name`: Name of the current session.

### Cocktail (beta)
Cocktail is multi-resource load testing/generation at once. You can generate loads of following forms:
1. Generate load to multiple REST endpoints at once.
2. Generate load to multiple SQS at once.
3. Generate load to SQS and REST Resources at once.

In a nutshell, you can mix and match any of the supported Resources while load testing.

We currently support upto 5 different types of Resources at once.





<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the Apache 2.0 License. See `LICENSE.txt` for more information.

Licenses of external dependency (as mention in `./pyproject.toml`) can be found in `./external_licenses.txt`

<p align="right">(<a href="#top">back to top</a>)</p>




<!-- MARKDOWN LINKS & IMAGES -->
[product-screenshot]: images/olaf_dashboard.png
© 2022
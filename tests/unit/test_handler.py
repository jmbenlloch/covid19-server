import json

import pytest

from covid_server import app

import collections

Parameters = collections.namedtuple('Parameters',
                                ['R0', 'T', 'Ti', 'days', 'Tm', 'M', 'Q', 'N', 'absolute'])

params = Parameters(
    R0   =   3.5,
    T    =   7,
    Ti   =   5,
    days = 100,
    Tm   =  15,
    M    =   0.35,
    Q    =  50,
    N    = 47e6,
    absolute = True)


@pytest.fixture()
def apigw_event():
    """ Generates API GW Event"""

    return {
        "body": '{ "days": 15}',
        "resource": "/{proxy+}",
        "requestContext": {
            "resourceId": "123456",
            "apiId": "1234567890",
            "resourcePath": "/{proxy+}",
            "httpMethod": "POST",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "accountId": "123456789012",
            "identity": {
                "apiKey": "",
                "userArn": "",
                "cognitoAuthenticationType": "",
                "caller": "",
                "userAgent": "Custom User Agent String",
                "user": "",
                "cognitoIdentityPoolId": "",
                "cognitoIdentityId": "",
                "cognitoAuthenticationProvider": "",
                "sourceIp": "127.0.0.1",
                "accountId": "",
            },
            "stage": "prod",
        },
        "queryStringParameters": {"foo": "bar"},
        "headers": {
            "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
            "Accept-Language": "en-US,en;q=0.8",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Mobile-Viewer": "false",
            "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
            "CloudFront-Viewer-Country": "US",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "X-Forwarded-Port": "443",
            "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
            "X-Forwarded-Proto": "https",
            "X-Amz-Cf-Id": "aaaaaaaaaae3VYQb9jd-nvCd-de396Uhbp027Y2JvkCPNLmGJHqlaA==",
            "CloudFront-Is-Tablet-Viewer": "false",
            "Cache-Control": "max-age=0",
            "User-Agent": "Custom User Agent String",
            "CloudFront-Forwarded-Proto": "https",
            "Accept-Encoding": "gzip, deflate, sdch",
        },
        "pathParameters": {"proxy": "/examplepath"},
        "httpMethod": "POST",
        "stageVariables": {"baz": "qux"},
        "path": "/examplepath",
    }



@pytest.fixture()
def request_sir(apigw_event):
    payload = {
        "model": "SIR",
        "params": {
            "R0"      : params.R0,
            "T"       : params.T,
            "Tm"      : params.Tm,
            "days"    : params.days,
            "Q"       : params.Q,
            "N"       : params.N,
            "absolute": params.absolute,
        }
    }

    apigw_event['body'] = json.dumps(payload)
    return apigw_event


@pytest.fixture()
def request_seir(apigw_event):
    payload = {
        "model": "SEIR",
        "params": {
            "R0"      : params.R0,
            "T"       : params.T,
            "Ti"      : params.Ti,
            "Tm"      : params.Tm,
            "days"    : params.days,
            "Q"       : params.Q,
            "N"       : params.N,
            "absolute": params.absolute,
        }
    }

    apigw_event['body'] = json.dumps(payload)
    return apigw_event


@pytest.fixture()
def request_beds(apigw_event):
    payload = {"model": "beds",
               "params": {
                   "R0": "3",
                   "T": "7",
                   "Ti": "5",
                   "days": "100",
                   "Tm" : "15",
                   "M" : "0.35",
               }
              }

    apigw_event['body'] = json.dumps(payload)
    return apigw_event


def test_sir(request_sir, mocker):

    ret = app.lambda_handler(request_sir, "")
    data = json.loads(ret["body"])

    assert ret["statusCode"] == 200
    assert len(data['t']) == params.days + 1
    assert len(data['S']) == params.days + 1
    assert len(data['I']) == params.days + 1
    assert len(data['R']) == params.days + 1


def test_seir(request_seir, mocker):

    ret = app.lambda_handler(request_seir, "")
    data = json.loads(ret["body"])

    assert ret["statusCode"] == 200
    assert len(data['t']) == params.days + 1
    assert len(data['S']) == params.days + 1
    assert len(data['E']) == params.days + 1
    assert len(data['I']) == params.days + 1
    assert len(data['R']) == params.days + 1

def test_beds(request_beds, mocker):

    ret = app.lambda_handler(request_beds, "")
    data = json.loads(ret["body"])

    assert ret["statusCode"] == 200
    assert len(data['t']) == params.days + 1

    assert len(data) == 20
    regions = ['Andalucía', 'Aragón', 'Asturias', 'Baleares', 'Canarias',
               'Cantabria', 'Cas-León', 'Cas-Mancha', 'Cataluña', 'Valencia',
               'Extremadura', 'Galicia', 'Madrid', 'Murcia', 'Navarra',
               'Euskadi', 'Rioja', 'Ceuta', 'Melilla']

    for region in regions:
        assert 'capacity' in data[region]
        assert  len(data[region]['camas']) == params.days + 1

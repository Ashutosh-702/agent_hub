import requests

BASE_URL = "http://localhost:8000/api/v1/orchestrated/run"



def main():

    response = requests.post(BASE_URL, json={
        "config": {
            "query": ""
        }
    })
    return

if __name__ == "__main__":
    main()

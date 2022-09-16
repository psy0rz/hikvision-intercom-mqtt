FROM python:3.8-buster

WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


# CMD [ "echo", "AAAAAAAAAA"]
# CMD [ "python", "a.py" ]

CMD [ "python", "-u", "hik.py" ]
# CMD [ "sleep", "10m" ]


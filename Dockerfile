FROM python:3.9-alpine as base

RUN apk add --no-cache --virtual .build-deps \
	gcc musl-dev

WORKDIR /app

# Install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install -r requirements.txt

# Production
FROM python:3.9-alpine

WORKDIR /app

COPY --from=base /opt/venv /opt/venv
COPY . .
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
CMD [ "python", "./dailies.py" ]

FROM python:3.11.2
ENV PYTHONUNBUFFERED=1
LABEL authors="felix"

ENTRYPOINT ["top", "-b"]
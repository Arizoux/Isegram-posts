FROM python:3.11.2
ENV PYTHONUNBUFFERED=1
LABEL authors="felix"
RUN pip install -r requirements.txt

ENTRYPOINT ["top", "-b"]
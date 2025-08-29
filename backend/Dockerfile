FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV FLASK_APP=/app/source/web_controller.py
EXPOSE 5000
CMD ["sh", "entrypoint.sh"]
FROM python:3.10-slim
ARG SKIP_COLLECTSTATIC=0

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN pip install jupyterlab ipykernel pandas

COPY . /app/

# SKIP_COLLECTSTATIC=1 のときは collectstatic を飛ばす
RUN if [ "$SKIP_COLLECTSTATIC" != "1" ]; then \
      python manage.py collectstatic --noinput; \
    fi

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
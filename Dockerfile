FROM python:3.6

RUN mkdir /hicetnunc-dataset
WORKDIR /hicetnunc-dataset

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src src
COPY scripts scripts
COPY dataset/fields_list.json dataset/fields_list.json
COPY config.py .
COPY cache.zip .

ENTRYPOINT [ "python", "./scripts/s0_run_all.py" ]

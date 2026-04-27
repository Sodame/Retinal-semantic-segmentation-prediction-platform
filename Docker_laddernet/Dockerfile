FROM continuumio/miniconda3:latest

WORKDIR /app

COPY requirements_conda.txt /app/requirements_conda.txt

RUN conda update -n base -c defaults conda -y && \
    conda config --add channels conda-forge && \
    conda config --add channels pytorch && \
    conda config --set channel_priority false

RUN conda create --name vesselseg --file /app/requirements_conda.txt -y && \
    conda clean --all --yes

COPY . /app

CMD ["conda", "run", "--no-capture-output", "-n", "vesselseg", "python", "app.py"]

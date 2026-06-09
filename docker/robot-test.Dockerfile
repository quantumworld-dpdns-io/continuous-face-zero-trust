FROM python:3.12-slim
RUN pip install --no-cache-dir robotframework robotframework-requests robotframework-jsonlibrary
WORKDIR /tests
COPY tests/robot/ /tests/robot/
COPY services/ /tests/services/
ENTRYPOINT ["robot"]
CMD ["--outputdir", "/tests/test-results", "/tests/robot/"]

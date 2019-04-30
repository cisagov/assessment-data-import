import logging
import os

# Local module
from adi import assessment_data_import as adi

# This Lambda function expects the following environment variables to be
# defined:
# 1. s3_bucket - The AWS S3 bucket containing the assessment data file
# 2. data_filename - The name of the file containing the assessment data in
# the S3 bucket above
# 3. db_hostname - The hostname that has the database to store the assessment
# data in
# 4. db_port - The port that the database server is listening on
# 5. ssm_db_name - The name of the parameter in AWS SSM that holds the name
# of the database to store the assessment data in.
# 6. ssm_db_user - The name of the parameter in AWS SSM that holds the
# database username with write permission to the assessment database.
# 7. ssm_db_password - The name of the parameter in AWS SSM that holds the
# database password for the user with write permission to the assessment
# database.

# In the case of AWS Lambda, the root logger is used BEFORE our Lambda handler
# runs, and this creates a default handler that goes to the console.  Once
# logging has been configured, calling logging.basicConfig() has no effect.  We
# can get around this by removing any root handlers (if present) before calling
# logging.basicConfig().  This unconfigures logging and allows --debug to
# affect the logging level that appears in the CloudWatch logs.
#
# See
# https://stackoverflow.com/questions/1943747/python-logging-before-you-run-logging-basicconfig
# and
# https://stackoverflow.com/questions/37703609/using-python-logging-with-aws-lambda
# for more details.
root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)

        # Set up logging
        log_level = logging.INFO
        logging.basicConfig(format='%(asctime)-15s %(levelname)s %(message)s',
                            level=log_level)


def handler(event, context):
    """Handle all Lambda events."""
    logging.debug('AWS Event was: {}'.format(event))

    # Get info in the S3 event notification message from
    # the parent Lambda function.
    record = event['Records'][0]

    # Verify event has correct eventName
    if record['eventName'] == 'ObjectCreated:Put':
        # Verify event originated from correct bucket and key
        if record['s3']['bucket']['name'] == os.environ['s3_bucket'] and \
           record['s3']['object']['key'] == os.environ['data_filename']:
            # Import the assessment data
            adi.import_data(s3_bucket=os.environ['s3_bucket'],
                            data_filename=os.environ['data_filename'],
                            db_hostname=os.environ['db_hostname'],
                            db_port=os.environ['db_port'],
                            ssm_db_name=os.environ['ssm_db_name'],
                            ssm_db_user=os.environ['ssm_db_user'],
                            ssm_db_password=os.environ['ssm_db_password'],
                            log_level=log_level)
        else:
            logging.warning('Expected ObjectCreated event from S3 bucket '
                            f"{os.environ['s3_bucket']} "
                            f"with key {os.environ['data_filename']}, but "
                            "received event from S3 bucket "
                            f"{record['s3']['bucket']['name']} with key "
                            f"{record['s3']['object']['key']}")
            logging.warning('Full AWS event: {}'.format(event))
    else:
        logging.warning('Unexpected eventName received: {}'.format(
            record['eventName']))
        logging.warning('Full AWS event: {}'.format(event))
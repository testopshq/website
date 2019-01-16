import boto3
import io
import zipfile
import mimetypes

def lambda_handler(event, context):
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-west-2:362637730868:deploySite')

    location = {
        "bucketName": "build.testops.co",
        "objectKey": "sitebuild.zip"
    }

    try:
        job = event.get("CodePipeline.job")

        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "MyAppBuild":
                    location = artifact["location"]["s3Location"]

        print("Building site from " + str(location))

        s3 = boto3.resource('s3')

        siteBuild_bucket = s3.Bucket(location["bucketName"])
        site_bucket = s3.Bucket('testops.co')

        site_zip = io.BytesIO()
        siteBuild_bucket.download_fileobj(location["objectKey"], site_zip)

        with zipfile.ZipFile(site_zip) as myzip:
            for nm in myzip.namelist():
                print(nm)
                obj = myzip.open(nm)
                fileType = mimetypes.guess_type(nm)[0]
                if fileType == None: fileType = 'text/html'
                site_bucket.upload_fileobj(obj, nm, ExtraArgs={'ContentType': fileType})
                site_bucket.Object(nm).Acl().put(ACL='public-read')
        print('Deployment done')
        topic.publish(Subject='testops.co deployed', Message='testops.co deployed susccesfully. The medium is the massage.')
        if job:
            codepipeline = boto3.client('codepipeline')
            codepipeline.put_job_success_result(jobId=job["id"])
    except:
        print('Deployment failed')
        topic.publish(Subject='testops.co failed to deploy', Message='testops.co deployment failed. The medium is the massage.')
        raise
    return 'Hello from Lambda'

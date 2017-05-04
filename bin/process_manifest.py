
# Contains the functions for downloading the contents of a manifest. 
#
# Author: James Matsumura
# Contact: jmatsumura@som.umaryland.edu

# base 2.7 lib(s)
import urllib2,hashlib,os,shutil
# additional dependencies (get from pip) 
import boto

# Accepts a manifest data structure which is a dict where the key is the unique
# ID of the file designated by OSDF. The value is then another dict which contains
# all URLs present as well as the MD5 for the file. 
def download_manifest(manifest,destination,priorities):
    
    # iterate over the manifest data structure, one ID/file at a time
    for key in manifest: 

        url = get_prioritized_endpoint(manifest[key]['urls'],priorities)

        file_name = "{0}/{1}".format(destination,url.split('/')[-1])

        if not os.path.exists(file_name): # only need to download if the file is not present

            tmp_file_name = "{0}.partial".format(file_name)

            # If we only have part of a file, get the new start position
            current_byte = 0

            if os.path.exists(tmp_file_name):
                current_byte = os.path.getsize(tmp_file_name)

            u = urllib2.urlopen(url)

            with open(tmp_file_name,'wb') as file:

                meta = u.info()
                file_size = int(meta.getheaders("Content-Length")[0])
                print("Downloading: {0} Bytes: {1}".format(file_name, file_size))

                file_size_dl = 0
                block_sz = 8192
                while True:
                    buffer = u.read(block_sz)
                    if not buffer:
                        break

                    file_size_dl += len(buffer)
                    file.write(buffer)
                    status = r"{0}  [{1:.2f}%]".format(file_size_dl, file_size_dl * 100. / file_size)
                    status = status + chr(8)*(len(status)+1)
                    print status,

            # If the download is complete, establish the final file
            if checksum_matches(tmp_file_name,manifest[key]['md5']):
                shutil.move(tmp_file_name,file_name)
            else:
                print("MD5 check failed.")

# Function to get the URL for the prioritized endpoint that the user requests.
# Note that priorities can be a list of ordered priorities 
def get_prioritized_endpoint(manifest_urls,priorities):

    chosen_url = ""

    urls = manifest_urls.split(',')
    eps = priorities.split(',')

    if eps[0] == "":
        eps = ['HTTP','FTP','S3','FASP'] # if none provided, use this order

    # Priorities are entered with highest first, so simply check until we find
    # a valid endpoint and then leave.
    for ep in eps:
        if chosen_url != "":
            break
        else:
            for url in urls:
                if url.startswith(ep.lower()):
                    chosen_url = url

    return chosen_url

# This function failing is largely telling that the data in OSDF for the
# particular file's MD5 is not correct.
def checksum_matches(file_path,original_md5):

    md5 = hashlib.md5()

    # Read the file in chunks and build a final MD5
    with open(file_path,'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)

    if md5.hexdigest() == original_md5:
        return True
    else:
        return False
        
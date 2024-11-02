# check params
if [ "$#" -ne 1 ]; then
    echo "usage: $0 <domain>"
    exit 1
fi

DOMAIN=$1

# VENV
python3.9 -m venv venv
source venv/bin/activate

# install packages
pip install --upgrade pip
pip install --upgrade setuptools
pip install -r requirements.txt


#GENERATE HOMESERVER CONFIG
python -m synapse.app.homeserver \
    --server-name $DOMAIN \
    --config-path homeserver.yaml \
    --generate-config \
    --report-stats=no

deactivate
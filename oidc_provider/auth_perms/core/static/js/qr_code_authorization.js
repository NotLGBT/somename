let currentTimerIdAndTypeOfRequest = {};

function generateQr(data, elementId){
    const qr = new VanillaQR({
        url: data,
        width: 600,
        height: 600,
        colorLight: "#ffffff",
        colorDark: "#000000",
        noBorder: true,
    });

    const imageElement = qr.toImage("png");

    if (imageElement) {
        const qr_html = document.getElementById(elementId)
        const oldQrImg = qr_html.getElementsByTagName('img')[0];

        if(oldQrImg) {
            qr_html.replaceChild(imageElement, oldQrImg)
        } else {

            switch (elementId) {
                case 'qrLogin':
                    qr_html.insertBefore(imageElement, document.getElementById('qrLoginExpired'))
                    break;
                case 'qrRegistration':
                    qr_html.insertBefore(imageElement, document.getElementById('qrRegistrationExpired'))
                    break;
                default:
                    qr_html.innerHTML = '';
                    qr_html.appendChild(imageElement)
            }
        }
    }
}


function emitQRToken(data) {
    const {qr_type} = data;
    const qrLoginExpired = document.getElementById('qrLoginExpired');
    const qrRegistrationExpired = document.getElementById('qrRegistrationExpired');

    let timeRange = 45; //period when the request will be sent (in sec)
    let startTime;

    const qrVisibilityFunc = (hide) => {
        switch (qr_type) {
            case 'authentication':
                timeRange = 45;
                qrLoginExpired.style.visibility = hide ? 'hidden' : 'visible';
                break;
            case 'registration':
                timeRange = 120;
                qrRegistrationExpired.style.visibility = hide ? 'hidden' : 'visible';
                break;
            default:
                break;
        }
        startTime = Date.now() + timeRange * 1000;
    }

    const getQrToken = async () => {
        try {
            const response = await fetch(qr_login_url, {
                method: 'POST',
                headers: json_headers,
                body: JSON.stringify(data)
            });
            if (response.status === 200) {
                const serviceCookie = await response.json(); // extract JSON from the http response
                saveSession(serviceCookie);
            }
        } catch (err) {
            console.log(err);
        } finally {
            const finishTime = Date.now();

            if (finishTime < startTime) {
                const timeout = qr_type == 'authentication' ? 2000 : 3000;
                currentTimerIdAndTypeOfRequest[qr_type] = setTimeout(getQrToken, timeout);
            } else {
                qrVisibilityFunc(false)
            }
        }
    }

    qrVisibilityFunc(true)
    clearTimeout(currentTimerIdAndTypeOfRequest[qr_type]);
    getQrToken();
}


// generate/start QR processing
emitQRToken(authentication_qr_token)
emitQRToken(registration_qr_token)

generateQr(authentication_content, "qrLogin")
generateQr(registration_content, "qrRegistration")


// updating qr code
const makeRequest = ({urlPath, qr_type, elementId}) => {
    let url = new URL(urlPath);
    params = {'qr_type': qr_type}
    Object.keys(params).forEach(key => url.searchParams.append(key, params[key]))

    fetch(url)
        .then(function(response){
            response.json()
                .then(
                    function(data) {
                        emitQRToken({
                            ...data,
                            qr_type
                        })
                        generateQr(JSON.stringify(data), elementId)
                    })
        })
}

const updateQrLoginFunc = () => makeRequest({
    elementId: 'qrLogin',
    urlPath: get_qr_url,
    qr_type: 'authentication'
});

const updateQrRegistrationFunc = () => makeRequest({
    elementId: 'qrRegistration',
    urlPath: get_qr_url,
    qr_type: 'registration'
});

document.getElementById("qrLoginExpired").onclick = updateQrLoginFunc;
document.getElementById("updateSignInQR").onclick = updateQrLoginFunc;

document.getElementById("qrRegistrationExpired").onclick = updateQrRegistrationFunc;
document.getElementById("updateSignUpQR").onclick = updateQrRegistrationFunc;


function saveSession(data) {
    if (data["session_token"] != undefined) {
        fetch(
            save_session_url,
            {
                method: "post",
                headers: json_headers,
                body: JSON.stringify({session_token: data['session_token']})
            }
        ).then(response => {
            response.json().then((json) => {
                document.cookie = service_name + "=" + data['session_token'] + "; path=/";

                const depended_promises = [];
                for (let service of depended_services) {
                    let session_key = service['name'].toLowerCase() + "_session_token";
                    if (data[session_key] != undefined) {
                        let session_data = {session_token: data[session_key]};
                        depended_promises.push(
                            new Promise(((resolve, reject) => {
                                fetch(service['save_session_url'], {
                                    method: "post",
                                    headers: json_headers,
                                    body: JSON.stringify(session_data)
                                })
                                .then(depended_response => {
                                    if (depended_response.ok) {
                                        depended_response.json().then((depended_response) => {
                                            document.cookie = service['name'] +"=" + data[session_key] + "; path=/";
                                            resolve();
                                        })
                                    }
                                    else {
                                        reject();
                                    }
                                })
                                .catch((err) => {
                                    console.log(err);
                                    resolve();
                                })
                            }))
                        )
                    }
                }
    
                Promise.all(depended_promises).then(() => {
                    if (json.redirect_to) {
                        window.location = json.redirect_to;
                    }
                    else {
                        afterSaveSession();
                    }
                })                
            })
        })
    }
}
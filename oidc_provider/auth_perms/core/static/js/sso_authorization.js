document.getElementById("ssoSignIn").onclick = make_sso_login;

function make_sso_login() {
    let data = {
        uuids: [],
        sessions: [],
        services: [],
        redirect_url: window.location.href,
    };
    fetch(sso_generation_url)
    .then(response => {
        response.json().then((response) => {
            data.uuids.push(response.uuid);
            data.sessions.push(response.session);
            document.cookie = "temporary_session=" + response["session"] + "; path=/";

            const depended_promises = [];

            for (let service of depended_services) {
                depended_promises.push(
                    new Promise(((resolve, reject) => {
                        fetch(service["sso_generation_url"])
                        .then(response => {
                            if (response.ok) {
                                response.json().then((response) => {
                                    data.uuids.push(response.uuid);
                                    data.sessions.push(response.session);
                                    data.services.push(response.service);
                                    document.cookie = "temporary_session_" + service['name'].toLowerCase() + "=" + response.session + "; path=/";
                                    resolve();
                                });
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

            Promise.all(depended_promises).then(() => {
                var form = document.createElement("form");
                form.action=response.domain;
                form.method="POST";
                var sessions=document.createElement("input");
                sessions.type="hidden";
                sessions.name="sessions";
                sessions.value= data.sessions;
                form.appendChild(sessions);
                var uuids=document.createElement("input");
                uuids.type="hidden";
                uuids.name="uuids";
                uuids.value = data.uuids;
                form.appendChild(uuids);
                var services=document.createElement("input");
                services.type="hidden";
                services.name="services";
                services.value = data.services;
                form.appendChild(services);
                var redirect_url=document.createElement("input");
                redirect_url.type="hidden";
                redirect_url.name="redirect_url";
                redirect_url.value = data.redirect_url;
                form.appendChild(redirect_url);
                document.body.appendChild(form);
                form.submit();
            });
        });
    });
    return false;
};


function checkTemporarySessionCookie() {
    let temporary_session_data = {
        temporary_session: getCookie("temporary_session"),
    }
    if (temporary_session_data.temporary_session) {
        deleteCookie("temporary_session");
        for (let service of depended_services) {
            let service_key = "temporary_session_" + service['name'].toLowerCase();
            let service_temporary_session = getCookie(service_key);
            if (service_temporary_session) {
                deleteCookie(service_key);
                temporary_session_data[service_key] = service_temporary_session;
            }
        }
        getSessionByTemporaryToken(temporary_session_data);
    }
}


function getSessionByTemporaryToken(data) {
    const getToken = async () => {
        try {
            const response = await fetch(sso_login_url, {
                method: 'POST',
                headers: json_headers,
                body: JSON.stringify(data)
            });
            if (response.status === 200) {
                const serviceCookie = await response.json();
                saveSession(serviceCookie['session_token'])
            }
        } catch (err) {
            console.log(err);
        }
    }
    getToken();
}

checkTemporarySessionCookie();
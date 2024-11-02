//Sign in form behavior
const signInEmailInput = document.getElementById('inputEmailSignIn')
const signInPasswordInput = document.getElementById('inputPassword')
const signInBtn = document.getElementById('btnSignInForm')

function setCredentialsFromUrlParams() {
    var email = (new URLSearchParams(window.location.search)).get("email");
    var login = (new URLSearchParams(window.location.search)).get("login");
    var password = (new URLSearchParams(window.location.search)).get("password");
    if (email) {
        signInEmailInput.value = email;
    }
    else if (login) {
        signInEmailInput.value = login;
    }
    if (password) {
        signInPasswordInput.value = password;
    }
}

setCredentialsFromUrlParams();

const checkSignInInputs = () => signInBtn.disabled = signInEmailInput.value.length === 0 || signInPasswordInput.value.length === 0;

signInEmailInput.oninput = () => checkSignInInputs();
signInPasswordInput.oninput = () => checkSignInInputs();

checkSignInInputs();

signInBtn.onclick = function () {
    let data = {
        actor_type: "classic_user"
    };
    let login_value = document.getElementById("inputEmailSignIn").value;
    if (login_value.includes('@')) {
        data['email'] = login_value;
    }
    else {
        data['login'] = login_value;
    }
    make_classic_login(data, document.getElementById("inputPassword").value)
    return false;
}

//Sign up form behavior
const firstNameSignUpInput = document.getElementById('inputFirstName')
const lastNameSignUpInput = document.getElementById('inputSurname')
const emailSignUpInput = document.getElementById('inputEmailSignUp')
const passwordSignUpInput = document.getElementById('inputPasswordSignUp')
const confirmPasswordSignUpInput = document.getElementById('inputPasswordSignUpConfirm')
const signUpBtn = document.getElementById('btnSignUpForm')

const checkSignUpInputs = () => {
    signUpBtn.disabled = firstNameSignUpInput.value.length === 0 ||
        lastNameSignUpInput.value.length === 0 ||
        emailSignUpInput.value.length === 0 ||
        passwordSignUpInput.value.length === 0 ||
        confirmPasswordSignUpInput.value.length === 0
}

firstNameSignUpInput.oninput = () => checkSignUpInputs();
lastNameSignUpInput.oninput = () => checkSignUpInputs();
emailSignUpInput.oninput = () => checkSignUpInputs();
passwordSignUpInput.oninput = () => checkSignUpInputs();
confirmPasswordSignUpInput.oninput = () => checkSignUpInputs();

checkSignUpInputs();

signUpBtn.onclick = function () {
    let data = {
        "uinfo": {
            "first_name": document.getElementById("inputFirstName").value,
            "last_name": document.getElementById("inputSurname").value
        },
        "password": document.getElementById("inputPasswordSignUp").value,
        "password_confirmation": document.getElementById("inputPasswordSignUpConfirm").value,
        "actor_type": "classic_user"
    }
    let login_value = document.getElementById("inputEmailSignUp").value;
    if (login_value.includes('@')) {
        data['email'] = login_value;
    }
    else {
        data['login'] = login_value;
    }
    requestPostMethod(registration_url, data)
    return false;
};



// Set cookie
function setCookie(name, value, days) {
    let expires = "";
    if (days) {
        let date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

// Function for getting value from cookie
function getCookie(cookie_name) {
    let name = cookie_name + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

// Delete temporary session from cookie
function deleteCookie(cookie_name) {
    document.cookie = cookie_name + '=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
}

// Default redirect function
function afterSaveSession(response) {
    window.location.replace(redirect_url_after_authentication)
}

// Notify functions
function newNotify(text, type) {
    const Notify = new XNotify("TopRight");
    Notify[type]({
        title: type.charAt(0).toUpperCase() + type.slice(1),
        description: text,
        duration: 4000
    });
}

function handleErrors(response) {
    if (!response.ok) {
        return Promise.reject(response);
    }
    return response.json();
}


// Functions with request

const json_headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

async function make_classic_login(data, password) {
    data['step'] = 'identification';
    
    await requestPostMethodPromise({
          url: authentication_url,
          data: data,
      }).then(async (response) => {
        let secret_data = {
            'step': 'check_secret',
            'actor_type': 'classic_user',
            'temporary_session': response['temporary_session'],
            'password': md5(md5(password) + response['temporary_session'])
        };

        requestPostMethodPromise({
            url: authentication_url,
            data: secret_data,
        }).then(async (response) => {
            document.cookie = service_name +"=" + response["session_token"] + "; path=/";
            
            if (depended_services) {
                let depended_temporary_sessions = {};
                let depended_indentification_requests = [];
                for (let i = 0; i < depended_services.length; i++) {
                    let service =  depended_services[i];
                    const depended_indentification_request = requestPostMethodPromise({
                        url: service['authentication_url'],
                        data: data,
                        noReject: true
                    }).then(depended_response => {
                        depended_temporary_sessions[service['name']] = depended_response['temporary_session'];
                    })
                    depended_indentification_requests.push(depended_indentification_request)
                }

                Promise.all(depended_indentification_requests).then(() => {
                    let depended_secret_requests = []
                    for (let i = 0; i < depended_services.length; i++) {
                        let service =  depended_services[i];
                        if (depended_temporary_sessions[service['name']]) {
                            let service_secret_data = {
                                'step': 'check_secret',
                                'actor_type': 'classic_user',
                                'temporary_session': depended_temporary_sessions[service['name']],
                                'password': md5(md5(password) + depended_temporary_sessions[service['name']])
                            };
                            const depended_secret_request = requestPostMethodPromise({
                                url: service['authentication_url'],
                                data: service_secret_data,
                                noReject: true
                            }).then(depended_response => {
                                document.cookie = service['name'] +"=" + depended_response["session_token"] + "; path=/";
                            })
                            depended_secret_requests.push(depended_secret_request)
                        }
                    }

                    Promise.all(depended_secret_requests).then(() => {
                        if (response.redirect_to) {
                            window.location = response.redirect_to;
                        } else {
                            afterSaveSession();
                        }
                    })
                })
            }
        })
    })
  };


let requestPostMethod = (url, data, callback) => {
    fetch(
        url,
        {
            method: "post",
            headers: json_headers,
            body: JSON.stringify(data)
        }
    ).then(handleErrors)
        .then(result => {
            newNotify(result.message, 'success')
            if(callback){
                callback()
            }
        })
        .catch(error => {
            error.json().then((json) => {
                newNotify(json.error_message || 'Something went wrong', 'error')
            })
        })
}

const requestPostMethodPromise = ({
    url,
    data,
    successNotifyFlag,
    noReject
}) => {
    return new Promise((resolve, reject) => {
        fetch(url, {
            method: "post",
            headers: json_headers,
            body: JSON.stringify(data)
        }).then(handleErrors).then(result => {
                if(successNotifyFlag) {
                    newNotify(result.message, 'success')
                }

                resolve(result)
            })
            .catch(error => {
                try {
                    error.json().then((json) => {
                        newNotify(json.error_message || 'Something went wrong', 'error')
                        if(noReject) {
                            resolve(json)
                        }
                    })
                }
                catch {
                    newNotify('Something went wrong', 'error')
                    if(noReject) {
                        resolve(error)
                    }
                    else {
                        reject(error)
                    }
                }
            })
    })
}

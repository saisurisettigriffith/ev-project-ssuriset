'use strict';

import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-auth.js";


window.addEventListener("load", function() {
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    updateUI(document.cookie);

    document.getElementById("sign-up").addEventListener('click', function() {
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        createUserWithEmailAndPassword(auth, email, password)
            .then((userCredential) => {
                const user = userCredential.user;
                user.getIdToken().then((token) => {
                    document.cookie = "token=" + token + ";path=/;SameSite=Strict;Secure";
                    window.location = "/";
                });
            })
            .catch((error) => {
                alert("Failed to sign up: " + error.message);
            });
    });

    document.getElementById("login").addEventListener('click', function() {
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        signInWithEmailAndPassword(auth, email, password)
            .then((userCredential) => {
                const user = userCredential.user;
                user.getIdToken().then((token) => {
                    document.cookie = "token=" + token + ";path=/;SameSite=Strict;Secure";
                    window.location = "/";
                });
            })
            .catch((error) => {
                alert("Failed to log in: " + error.message);
            });
    });

    document.getElementById("sign-out").addEventListener('click', function() {
        signOut(auth)
            .then((output) => {
                document.cookie = "token=;path=/;SameSite=Strict";
                window.location = "/";
            });
    });


    // My code //
    // New methods learned - .includes() and .style.display //
    // Not sure if I should be using "this.value" or "this.options[this.selectedIndex].value" //
    document.querySelector('select[name="attribute_name"]').addEventListener('change', function() {
        var isNumeric = ['year', 'battery_size', 'wltp_range', 'cost', 'power'].includes(this.options[this.selectedIndex].value);
        if (isNumeric) {
            document.getElementById('string_value_case_1').style.display = 'none';
            document.getElementById('min_value_case_2').style.display = 'inline';
            document.getElementById('max_value_case_2').style.display = 'inline';
        } else {
            document.getElementById('string_value_case_1').style.display = 'inline';
            document.getElementById('min_value_case_2').style.display = 'none';
            document.getElementById('max_value_case_2').style.display = 'none';
        }
    });

    selectElement.dispatchEvent(new Event('change'));

});

// My code - stackoverflow, google//
document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    const compareButton = document.getElementById('compare-btn');
    const checkboxes = document.querySelectorAll('.ev-checkbox');

    const updateFormState = () => {

        // JS way of doing things - learned that we can us ".ev-checkbox:checked" to get all checked checkboxes //
        const checkedCheckboxes = document.querySelectorAll('.ev-checkbox:checked');
        
        // If and *only if* 2 check-boxes are selected - exactly 2 //
        if (checkedCheckboxes.length === 2) {
            compareButton.disabled = false;
        } else {
            compareButton.disabled = true;
        }
        
        // In html, we are using a form, and forms take in input elements, so we have to create input elements and append them to the form //
        //
        for (var i = 0; i < checkedCheckboxes.length; i++) {
            var input = document.createElement('input'); // Dynamic //
            input.setAttribute('type', 'hidden');
            var inputName = 'ev_id_' + (i + 1);
            input.setAttribute('name', inputName);
            input.setAttribute('value', checkedCheckboxes[i].value);
            form.appendChild(input); // Dynamic //
        }
        // It is ready to be sent out to the server //
        
    };
    // What if the user selects 2 checkboxes and then unchecks one of them before selecting another 2nd row? We have to keep updating whenever change triggers //
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateFormState);
    });
});


// Barry Denby's code //
//
//
//
function updateUI(cookie) {
    var token = parseCookieToken(cookie);

    if (token.length > 0) {
        document.getElementById("login-box").hidden = true;
        document.getElementById("sign-out").hidden = false;
    } else {
        document.getElementById("login-box").hidden = false;
        document.getElementById("sign-out").hidden = true;
    }
}

function parseCookieToken(cookie) {
    var strings = cookie.split(';');
    for (let i = 0; i < strings.length; i++) {
        var temp = strings[i].split('=');
        if (temp[0] == "token") {
            return temp[1];
        }
    }
    return "";
}
//
//
// Barry Denby's code //
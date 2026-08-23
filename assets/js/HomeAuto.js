/**********************************************************************
 * HomeAuto.js
 * Part 1
 * Rendering Engine
 **********************************************************************/

let selectedHouseIndex = 0;
let selectedRoomIndex = 0;

let deviceModal = null;

document.addEventListener("DOMContentLoaded", () => {

    deviceModal = new bootstrap.Modal(
        document.getElementById("deviceModal")
    );

    initialiseHomeAutomation();

});


/**********************************************************************
 * INITIALISE
 **********************************************************************/

function initialiseHomeAutomation() {

    const houseSelector = document.getElementById("houseSelector");

    houseSelector.addEventListener("change", function () {

        selectedHouseIndex = parseInt(this.value);

        selectedRoomIndex = 0;

        renderRooms();

        renderDevices();

    });

    renderRooms();

    renderDevices();

}


/**********************************************************************
 * CURRENT HOUSE
 **********************************************************************/

function getCurrentHouse() {

    return HOUSES[selectedHouseIndex];

}


/**********************************************************************
 * CURRENT ROOM
 **********************************************************************/

function getCurrentRoom() {

    return getCurrentHouse().rooms[selectedRoomIndex];

}


/**********************************************************************
 * RENDER ROOM CAROUSEL
 **********************************************************************/

function renderRooms() {

    const carousel = document.getElementById("roomCarousel");

    carousel.innerHTML = "";

    const rooms = getCurrentHouse().rooms;

    rooms.forEach((room, index) => {

        const card = document.createElement("div");

        card.className =
            "room-card " +
            (index === selectedRoomIndex ? "active" : "");

        card.innerHTML = `
            <div class="room-symbol">
                ${room.name.charAt(0)}
            </div>

            <strong>${room.name}</strong>

            <span>${room.devices.length} Actions</span>
        `;

        card.onclick = function () {

            selectedRoomIndex = index;

            renderRooms();

            renderDevices();

        };

        carousel.appendChild(card);

    });

}


/**********************************************************************
 * GROUP DEVICES
 **********************************************************************/

function groupDevices(deviceList) {

    const grouped = {};

    deviceList.forEach(device => {

        if (!grouped[device.device_name]) {

            grouped[device.device_name] = [];

        }

        grouped[device.device_name].push(device);

    });

    return grouped;

}


/**********************************************************************
 * RENDER DEVICES
 **********************************************************************/

function renderDevices() {

    const room = getCurrentRoom();

    document.getElementById("currentRoomTitle").innerHTML =
        room.name + " Devices";

    const container =
        document.getElementById("deviceContainer");

    container.innerHTML = "";

    const grouped =
        groupDevices(room.devices);

    Object.keys(grouped).forEach(deviceName => {

        const actions =
            grouped[deviceName];

        container.appendChild(

            createDeviceCard(
                deviceName,
                actions
            )

        );

    });

}


/**********************************************************************
 * CREATE DEVICE CARD
 **********************************************************************/

function createDeviceCard(deviceName, actions) {

    const card = document.createElement("div");

    card.className = "device-card";

    const first = actions[0];

    let buttons = "";

    actions.forEach(action => {

        buttons += `
        <button
            class="command"
            onclick="triggerAction(
                '${action.uid}',
                '${action.device_name}',
                '${action.action}'
            )">

            ${action.action}

        </button>
        `;

    });

    card.innerHTML = `

        <div class="card-actions">

            <button
                class="btn-icon edit-btn"

                onclick="openModalForEdit(
                    '${first.uid}',
                    '${escapeHtml(first.device_name)}',
                    '${escapeHtml(first.room)}',
                    '${escapeHtml(first.House)}',
                    '${escapeHtml(first.action)}',
                    '${escapeHtml(first.api_url)}',
                    '${first.display_order}'
                )">

                <i class="bi bi-pencil-fill"></i>

            </button>

            <button
                class="btn-icon delete-btn"

                onclick="deleteDevice(
                    '${first.uid}',
                    '${escapeHtml(first.device_name)}'
                )">

                <i class="bi bi-trash-fill"></i>

            </button>

        </div>

        <div class="device-top">

            <div>

                <h3>

                    ${deviceName}

                </h3>

                <div class="status-badge">

                    <div class="status-dot"></div>

                    Online

                </div>

            </div>

            <div class="device-icon">

                ${getDeviceIcon(deviceName)}

            </div>

        </div>

        <div class="command-row">

            ${buttons}

        </div>

    `;

    return card;

}


/**********************************************************************
 * DEVICE ICON
 **********************************************************************/

function getDeviceIcon(name) {

    const lower = name.toLowerCase();

    if (lower.includes("fan"))
        return "🌀";

    if (lower.includes("lamp"))
        return "💡";

    if (lower.includes("light"))
        return "💡";

    if (lower.includes("tv"))
        return "📺";

    if (lower.includes("door"))
        return "🚪";

    if (lower.includes("curtain"))
        return "🪟";

    if (lower.includes("ac"))
        return "❄️";

    return "⚙️";

}


/**********************************************************************
 * HTML ESCAPE
 **********************************************************************/

function escapeHtml(text) {

    if (text === null || text === undefined)
        return "";

    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}

/**********************************************************************
 * HomeAuto.js
 * Part 2
 * CRUD Operations
 **********************************************************************/

const csrfToken = document.querySelector(
    "[name=csrfmiddlewaretoken]"
).value;

const fetchHeaders = {
    "Content-Type": "application/json",
    "X-CSRFToken": csrfToken
};


/**********************************************************************
 * REGISTER EVENTS
 **********************************************************************/

document.addEventListener("DOMContentLoaded", () => {

    document
        .getElementById("deviceForm")
        .addEventListener(
            "submit",
            handleFormSubmit
        );

});


/**********************************************************************
 * OPEN CREATE MODAL
 **********************************************************************/

function openModalForCreate() {

    document.getElementById("deviceForm").reset();

    document.getElementById("formMode").value = "create";

    document.getElementById("deviceUid").value = "";

    document.getElementById("modalTitle").innerHTML =
        "Add Device";

    document.getElementById("inputHouse").value =
        getCurrentHouse().house;

    document.getElementById("inputRoom").value =
        getCurrentRoom().name;

    document.getElementById("inputOrder").value = 1;

    document.getElementById("inputActive").checked = true;

    deviceModal.show();

}


/**********************************************************************
 * OPEN EDIT MODAL
 **********************************************************************/

function openModalForEdit(
    uid,
    deviceName,
    room,
    house,
    action,
    apiUrl,
    order
) {

    document.getElementById("formMode").value = "edit";

    document.getElementById("deviceUid").value = uid;

    document.getElementById("inputHouse").value = house;

    document.getElementById("inputRoom").value = room;

    document.getElementById("inputName").value = deviceName;

    document.getElementById("inputAction").value = action;

    document.getElementById("inputApiUrl").value = apiUrl;

    document.getElementById("inputOrder").value = order;

    document.getElementById("inputActive").checked = true;

    document.getElementById("modalTitle").innerHTML =
        "Edit Device";

    deviceModal.show();

}


/**********************************************************************
 * FORM SUBMIT
 **********************************************************************/

async function handleFormSubmit(e) {

    e.preventDefault();

    const mode =
        document.getElementById("formMode").value;

    const uid =
        document.getElementById("deviceUid").value;

    const payload = {

        House:
            document.getElementById("inputHouse").value,

        room:
            document.getElementById("inputRoom").value,

        device_name:
            document.getElementById("inputName").value,

        action:
            document.getElementById("inputAction").value,

        api_url:
            document.getElementById("inputApiUrl").value,

        display_order:
            parseInt(
                document.getElementById("inputOrder").value
            ),

        is_active:
            document.getElementById("inputActive").checked

    };

    const url =
        mode === "create"
            ? CRUD_API_URL
            : CRUD_API_URL + uid + "/";

    const method =
        mode === "create"
            ? "POST"
            : "PUT";

    try {

        logToConsole(
            "Saving device..."
        );

        const response =
            await fetch(url, {

                method,

                headers: fetchHeaders,

                body: JSON.stringify(payload)

            });

        if (!response.ok) {

            const err =
                await response.json();

            throw err;

        }

        logToConsole(
            "Configuration Saved Successfully."
        );

        deviceModal.hide();

        setTimeout(() => {

            location.reload();

        }, 800);

    }

    catch (error) {

        console.error(error);

        logToConsole(
            "Failed to save configuration.",
            true
        );

    }

}


/**********************************************************************
 * DELETE DEVICE
 **********************************************************************/

async function deleteDevice(
    uid,
    deviceName
) {

    if (
        !confirm(
            "Delete " +
            deviceName +
            " ?"
        )
    )
        return;

    try {

        logToConsole(
            "Deleting " +
            deviceName
        );

        const response =
            await fetch(
                CRUD_API_URL +
                uid +
                "/",
                {

                    method: "DELETE",

                    headers: fetchHeaders

                }
            );

        if (
            response.ok ||
            response.status === 204
        ) {

            logToConsole(
                "Deleted Successfully."
            );

            setTimeout(() => {

                location.reload();

            }, 700);

        }

        else {

            throw response.status;

        }

    }

    catch (error) {

        console.error(error);

        logToConsole(
            "Delete Failed.",
            true
        );

    }

}


/**********************************************************************
 * DUPLICATE DEVICE
 **********************************************************************/

async function duplicateDevice(device) {

    const payload = {

        House: device.House,

        room: device.room,

        device_name: device.device_name,

        action: device.action,

        api_url: device.api_url,

        display_order:
            device.display_order,

        is_active: true

    };

    try {

        const response =
            await fetch(
                CRUD_API_URL,
                {

                    method: "POST",

                    headers: fetchHeaders,

                    body: JSON.stringify(payload)

                }
            );

        if (response.ok) {

            logToConsole(
                "Duplicated Successfully"
            );

            setTimeout(() => {

                location.reload();

            }, 800);

        }

    }

    catch (e) {

        console.error(e);

        logToConsole(
            "Duplicate Failed",
            true
        );

    }

}


/**********************************************************************
 * CLOSE MODAL
 **********************************************************************/

function closeModal() {

    deviceModal.hide();

}


/**********************************************************************
 * RESET FORM
 **********************************************************************/

function resetDeviceForm() {

    document
        .getElementById("deviceForm")
        .reset();

    document
        .getElementById("deviceUid")
        .value = "";

    document
        .getElementById("formMode")
        .value = "create";

}

/**********************************************************************
 * HomeAuto.js
 * Part 3
 * Action Engine & Utilities
 **********************************************************************/


/**********************************************************************
 * TRIGGER DEVICE ACTION
 **********************************************************************/

/**********************************************************************
 * TRIGGER DEVICE ACTION
 **********************************************************************/

async function triggerAction(
    uid,
    deviceName,
    actionName
) {

    logToConsole(
        `Executing '${actionName}' on ${deviceName}...`
    );

    setButtonLoading(uid, true);

    try {

        // 1. FIRST API CALL (Get the URL from your backend)
        const response = await fetch(
            ACTION_API_URL,
            {
                method: "POST",
                headers: fetchHeaders,
                body: JSON.stringify({
                    uid: uid
                })
            }
        );

        const data = await response.json();

        if (response.ok) {

            logToConsole(
                data.message ||
                `URL retrieved for ${deviceName}`
            );

            flashDeviceCard(uid);

            // 2. SECOND API CALL (Trigger the actual device URL)
            // 2. SECOND API CALL (Trigger the actual device URL)
            if (data.api_url) {

                logToConsole("Triggering device URL...");

                try {
                    // ADD mode: 'no-cors' HERE
                    await fetch(data.api_url, {
                        method: "GET",
                        mode: "no-cors"
                    });

                    // NOTE: Because of 'no-cors', we cannot use .text() or .json()
                    // to read the response. The browser hides it for security.

                    console.log("--- VIRTUAL SMART HOME RESPONSE ---");
                    console.log(`Device: ${data.device_name} | Action: ${data.action_name}`);
//                    console.log("URL Fetched:", data.api_url);
                    console.log("Status: Request sent successfully (Opaque response due to CORS)");
                    console.log("-----------------------------------");

                    logToConsole("Device triggered successfully!");

                } catch (deviceError) {
                    console.error("Error triggering external URL:", deviceError);
                    logToConsole("Failed to reach the external device URL.", true);
                }

            }

        }
        else {

            logToConsole(
                data.message ||
                "Command Failed",
                true
            );

        }

    }
    catch (error) {

        console.error(error);

        logToConsole(
            "Unable to reach automation server.",
            true
        );

    }

    setButtonLoading(uid, false);

}

/**********************************************************************
 * API CONSOLE
 **********************************************************************/

function logToConsole(
    message,
    isError = false
) {

    const consoleBox =
        document.getElementById(
            "console-output"
        );

    const time =
        new Date().toLocaleTimeString();

    consoleBox.innerHTML =
        `[${time}] ${message}`;

    consoleBox.style.color =
        isError
            ? "#ff5f6d"
            : "#6EE7B7";

}


/**********************************************************************
 * BUTTON LOADING
 **********************************************************************/

function setButtonLoading(
    uid,
    loading
) {

    const buttons =
        document.querySelectorAll(
            ".command"
        );

    buttons.forEach(btn => {

        const onclick =
            btn.getAttribute("onclick");

        if (
            onclick &&
            onclick.includes(uid)
        ) {

            btn.disabled = loading;

            if (loading) {

                btn.dataset.oldText =
                    btn.innerHTML;

                btn.innerHTML =
                    `<span class="spinner-border spinner-border-sm"></span>`;

            }
            else {

                btn.innerHTML =
                    btn.dataset.oldText;

            }

        }

    });

}


/**********************************************************************
 * CARD FLASH
 **********************************************************************/

function flashDeviceCard(uid) {

    const buttons =
        document.querySelectorAll(
            ".command"
        );

    buttons.forEach(btn => {

        const onclick =
            btn.getAttribute("onclick");

        if (
            onclick &&
            onclick.includes(uid)
        ) {

            const card =
                btn.closest(".device-card");

            if (!card)
                return;

            card.classList.add(
                "device-success"
            );

            setTimeout(() => {

                card.classList.remove(
                    "device-success"
                );

            }, 900);

        }

    });

}


/**********************************************************************
 * REFRESH UI
 **********************************************************************/

function refreshCurrentRoom() {

    renderRooms();

    renderDevices();

}


/**********************************************************************
 * FIND DEVICE
 **********************************************************************/

function findDeviceByUID(uid) {

    const rooms =
        getCurrentHouse().rooms;

    for (const room of rooms) {

        for (const device of room.devices) {

            if (device.uid == uid)
                return device;

        }

    }

    return null;

}


/**********************************************************************
 * GET ROOM BY NAME
 **********************************************************************/

function getRoom(roomName) {

    const rooms =
        getCurrentHouse().rooms;

    return rooms.find(
        r => r.name === roomName
    );

}


/**********************************************************************
 * HOUSE BY NAME
 **********************************************************************/

function getHouse(name) {

    return HOUSES.find(
        h => h.house === name
    );

}


/**********************************************************************
 * TOAST
 **********************************************************************/

function showToast(
    message,
    success = true
) {

    logToConsole(
        message,
        !success
    );

}


/**********************************************************************
 * SORT DEVICES
 **********************************************************************/

function sortDevices(actions) {

    actions.sort(function (a, b) {

        return (
            a.display_order -
            b.display_order
        );

    });

    return actions;

}


/**********************************************************************
 * GROUP + SORT
 **********************************************************************/

function groupDevices(deviceList) {

    const grouped = {};

    deviceList.forEach(device => {

        if (!grouped[device.device_name]) {

            grouped[device.device_name] = [];

        }

        grouped[
            device.device_name
        ].push(device);

    });

    Object.keys(grouped).forEach(key => {

        grouped[key] =
            sortDevices(grouped[key]);

    });

    return grouped;

}


/**********************************************************************
 * SEARCH DEVICE
 **********************************************************************/

function searchDevices(keyword) {

    keyword =
        keyword.toLowerCase();

    const room =
        getCurrentRoom();

    return room.devices.filter(device =>

        device.device_name
            .toLowerCase()
            .includes(keyword)

    );

}


/**********************************************************************
 * FILTER ACTIVE
 **********************************************************************/

function activeDevices() {

    return getCurrentRoom()
        .devices
        .filter(d => d.is_active);

}


/**********************************************************************
 * REFRESH AFTER CRUD
 **********************************************************************/

function reloadAfterDelay(
    delay = 700
) {

    setTimeout(() => {

        location.reload();

    }, delay);

}


/**********************************************************************
 * KEYBOARD SHORTCUTS
 **********************************************************************/

document.addEventListener(
    "keydown",
    function (e) {

        if (
            e.ctrlKey &&
            e.key === "n"
        ) {

            e.preventDefault();

            openModalForCreate();

        }

        if (
            e.key === "Escape"
        ) {

            if (deviceModal) {

                deviceModal.hide();

            }

        }

    }
);


/**********************************************************************
 * APPLICATION READY
 **********************************************************************/

console.log(
    "SmartDash HomeAuto.js Loaded Successfully."
);

logToConsole(
    "System Ready."
);
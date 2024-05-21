// Firebase configuration
const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_AUTH_DOMAIN",
    databaseURL: "YOUR_DATABASE_URL",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_STORAGE_BUCKET",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const database = firebase.database();

// Function to fetch data from Firebase and display in the table
function fetchData() {
    const dataTableBody = document.getElementById('data-table-body');
    dataTableBody.innerHTML = ''; // Clear the table body

    database.ref('your_data_path').once('value', (snapshot) => {
        let index = 1;
        snapshot.forEach((childSnapshot) => {
            const data = childSnapshot.val();
            const row = document.createElement('tr');
            
            const cellNo = document.createElement('td');
            cellNo.textContent = index++;
            row.appendChild(cellNo);

            const cellName = document.createElement('td');
            cellName.textContent = data.name;
            row.appendChild(cellName);

            const cellScore = document.createElement('td');
            cellScore.textContent = data.score;
            row.appendChild(cellScore);

            dataTableBody.appendChild(row);
        });
    });
}

// Fetch data on page load
window.onload = fetchData;

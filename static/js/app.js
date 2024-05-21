import { initializeApp } from "https://www.gstatic.com/firebasejs/9.8.1/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/9.8.1/firebase-analytics.js";
import { getDatabase } from "https://www.gstatic.com/firebasejs/9.8.1/firebase-database.js";

const firebaseConfig = {
    apiKey: "AIzaSyBTrpCbKI_xdf6qL4JMe0PzcspWegfZLLk",
    authDomain: "cs402-1c97e.firebaseapp.com",
    databaseURL: "https://cs402-1c97e-default-rtdb.europe-west1.firebasedatabase.app",
    projectId: "cs402-1c97e",
    storageBucket: "cs402-1c97e.appspot.com",
    messagingSenderId: "129609008324",
    appId: "1:129609008324:web:b53a99cf86132730c13591",
    measurementId: "G-FB167SZPLZ"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

async function fetchData() {
    const dataTableBody = document.getElementById('data-table-body');
    dataTableBody.innerHTML = ''; // Clear the table body

    try {
        const response = await axios.get(`https://cs402-1c97e-default-rtdb.europe-west1.firebasedatabase.app/.json`);
        const data = response.data;
        console.log(response.status)
        console.log(response)
        
        let index = 1;
        for (const [key, value] of Object.entries(data)) {
            const row = document.createElement('tr');
            
            const cellNo = document.createElement('td');
            cellNo.textContent = index++;
            row.appendChild(cellNo);

            const cellName = document.createElement('td');
            const link = document.createElement('a');
            link.href = value.url;
            link.target = "_blank"; // Open in a new tab
            link.textContent = value.url;
            cellName.appendChild(link);
            row.appendChild(cellName);


            const cellScore = document.createElement('td');
            cellScore.textContent = value.total_grades_sum || "N/A"; // Adjust based on your data structure
            row.appendChild(cellScore);

            dataTableBody.appendChild(row);
        }
    } catch (error) {
        console.error("Error fetching data: ", error);
    }
}

// Fetch data on page load
window.onload = fetchData;




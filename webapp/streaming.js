
class Queue {
    constructor() {
        this.items = [];
    }

    enqueue(item) {
        this.items.push(item);
    }

    dequeue() {
    if (this.items.length === 0) {
        return null;
    }
        return this.items.shift();
    }

    isEmpty() {
        return this.items.length === 0;
    }
}

let audioContext;
let mediaStream;
let socket;
let scriptProcessor;
let pieChart;
let intervalId;
let aggregatedShares = {};

const queue = new Queue();

function aggregateShares() {
    while(!queue.isEmpty()) {
        data = JSON.parse(queue.dequeue())
        data.forEach(([key, value]) => {
            if (aggregatedShares[key]) {
                aggregatedShares[key] += value;
            } else {
                aggregatedShares[key] = value;
            }
        });
    }
    drawPie(aggregatedShares)
}

function startStreaming() {

    socket = new WebSocket('ws://127.0.0.1:7007'); 

    socket.onopen = function() {
        console.log('WebSocket connection opened');
    };
    socket.onclose = function() {
        console.log('WebSocket connection closed');
    };
    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
    socket.onmessage = function(event) {
        queue.enqueue(event.data)
        console.log(event.data)
    };

    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        mediaStream = stream;

        scriptProcessor = audioContext.createScriptProcessor(4096, 1, 1);
        
        const source = audioContext.createMediaStreamSource(stream);
        source.connect(scriptProcessor);
        scriptProcessor.connect(audioContext.destination);

        scriptProcessor.onaudioprocess = function(event) {
            const inputBuffer = event.inputBuffer.getChannelData(0);
            
            const base64String = float32ToBase64(inputBuffer);

            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(base64String);
            }
        };
    }).catch(err => {
        console.error('Error accessing microphone:', err);
        stopStreaming();
    });

    intervalId = setInterval(aggregateShares, 3000);
}

function stopStreaming() {

    if(intervalId) {
        clearInterval(intervalId);
    }

    if (scriptProcessor) {
        scriptProcessor.disconnect();
        scriptProcessor = null;
    }

    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }

    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }

    if (socket) {
        socket.close();
        socket = null;
    }
}

function handleToggle() {

    button = document.getElementById('toggleButton')
    if(button.textContent === 'Start conversation') {
        startStreaming();
        document.getElementById('toggleButton').textContent = 'Stop conversation';
    } else {
        stopStreaming();
        document.getElementById('toggleButton').textContent = 'Start conversation';
    }
}

function resetConversation() {
    
    aggregatedShares = {}
    drawPie(aggregatedShares)
}

function drawPie(data) {

    let labels = Object.keys(data)
    let timeshares = Object.values(data)

    if(pieChart == null) {
        const ctx = document.getElementById('chartjsPieChart').getContext('2d');
        pieChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: timeshares,
                    backgroundColor: ["#FFB3BA","#FFDFBA","#FFFFBA","#BAFFC9","#BAE1FF","#D4A5A5","#D4B5E8","#FFB7CE","#C4FCEF","#FFE5CC"]
                }]
            }
        });
    } else {
        pieChart.data.labels = labels;
        pieChart.data.datasets[0].data = timeshares;
        pieChart.update();
    }
}

function float32ToBase64(float32Array) {
    const bytes = new Uint8Array(float32Array.buffer);
    return btoa(String.fromCharCode.apply(null, bytes));
}
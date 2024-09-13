
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

let audioContext = null;
let mediaStream = null;
let socket = null;
let scriptProcessor = null;

let pieChart = null;
let intervalId = null;
let aggregatedShares = { };

const QUEUE = new Queue();
const AGGREGATION_INTERVAL = 3000
const PIE_ANIMATION_DURATION = 3000
const PIE_COLORS = [
    '#FFB3BA',
    '#BAFFC9',
    '#FFFFBA',
    '#BAE1FF',
    '#CBAACB',
    '#FFDAC1',
    '#B5EAD7',
    '#E2F0CB',
    '#FF9AA2',
    '#FDFD96',
    '#A1CAF1',
    '#FFCBF2',
    '#E0BBE4',
    '#D4A5A5',
    '#FDE2E4',
    '#C1E1C1',
    '#C4DEF6',
    '#FAD2E1',
    '#F5E1DA',
    '#FFDFBA',
]
const SLIDERS = [
    {'id': 'TauActive', 'min': 0, 'max': 1.0, 'step': 0.05},
    {'id': 'RhoUpdate', 'min': 0, 'max': 1.0, 'step': 0.05},
    {'id': 'DeltaNew', 'min': 0, 'max': 2.0, 'step': 0.05},
    {'id': 'MaxSpeakers', 'min': 1, 'max': 20, 'step': 1}
]

function aggregateShares() {
    while(!QUEUE.isEmpty()) {
        data = JSON.parse(QUEUE.dequeue())
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

function startModelIfNeeded(started_handler) {
    $.get('/speequal/status', function(data) {
        if(data.status) {
            started_handler();
        } else {
            $.get('/speequal/start', started_handler);
        }
    });
}

function resetModel() {
    $.get('/speequal/reset').always(function() {
        aggregatedShares = { };
        drawPie(aggregatedShares);
    });
}

function updateConfig() {
    $.get('/speequal/config/update', $('#configForm').serialize(), function() { resetModel(); });
}

function startStreaming() {
    socket = new WebSocket('ws://' + $('#valueWebsocketServer').val()); 

    socket.onopen = function() {
        console.log('WebSocket opened');
    };
    socket.onclose = function() {
        console.log('WebSocket closed');
        stopStreaming();
    };
    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
    socket.onmessage = function(event) {
        QUEUE.enqueue(event.data)
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

        intervalId = setInterval(aggregateShares, AGGREGATION_INTERVAL);

    }).catch(error => {
        console.error('Error accessing microphone:', error);
        stopStreaming();
    });
}

function stopStreaming() {
    try {
        if(intervalId) {
            clearInterval(intervalId);
            intervalId = null
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
    } finally {
        $('#startButton').show();
        $('#stopButton').hide();
    }
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
                    backgroundColor: PIE_COLORS
                }]
            },
            options: {
                animation: {
                    duration: PIE_ANIMATION_DURATION
                }
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

$(document).ready(function() {
    
    $('#startButton').click(function() {
        $(this).hide();
        $('#stopButton').show();
        startModelIfNeeded(function() {
            startStreaming();
        });
    });

    $('#stopButton').click(function() {
        stopStreaming();
    });

    $('#resetButton').click(function() {
        resetModel();
    });

    $('#configButton').click(function() {
        $('#configContainer').slideToggle();
    });

    $('#configUpdateButton').click(function(e) {
        e.preventDefault();
        updateConfig();
    });

    $.get('/speequal/config/get', function(config) {
        SLIDERS.forEach(function(slider) { 
            configValue = config[$('#value' + slider.id).attr('name')];
            $('#value' + slider.id).val(configValue);
            $('#slider' + slider.id).slider({
                value: configValue,
                min: slider.min,
                max: slider.max,
                step: slider.step,
                slide: function(event, ui) {
                    $('#value' + slider.id).val(ui.value);
                }
            });        
        });
    });

});
let mediaRecorder;
let audioChunks = [];

document.getElementById('start-recording').addEventListener('click', async () => {
    try {
        let stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = function(event) {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = function() {
            let audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            let audioURL = URL.createObjectURL(audioBlob);
            document.getElementById('audio-playback').src = audioURL;

            // 오디오 파일을 서버로 전송
            let formData = new FormData();
            formData.append('audio_data', audioBlob, 'audio.wav');

            fetch('/upload_audio', {
                method: 'POST',
                body: formData,
            })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('response').textContent = data.response || data.error;
                })
                .catch(err => {
                    console.error('Error uploading audio:', err);
                    alert('Error uploading audio. Please try again.');
                });
        };

        mediaRecorder.start();
        document.getElementById('start-recording').disabled = true;
        document.getElementById('stop-recording').disabled = false;
    } catch (err) {
        console.error('Error accessing media devices.', err);
        alert('Error accessing your microphone. Please check your permissions.');
    }
});

document.getElementById('stop-recording').addEventListener('click', () => {
    if (mediaRecorder) {
        mediaRecorder.stop();
        document.getElementById('start-recording').disabled = false;
        document.getElementById('stop-recording').disabled = true;
        audioChunks = [];
    } else {
        console.error('MediaRecorder not initialized.');
    }
});

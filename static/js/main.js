document.addEventListener('DOMContentLoaded', function() {
    const voiceSelect = document.getElementById('voice-select');
    const textInput = document.getElementById('text-input');
    const generateBtn = document.getElementById('generate-btn');
    const audioContainer = document.getElementById('audio-container');
    const audioPlayer = document.getElementById('audio-player');
    const statusDiv = document.getElementById('status');

    // 加载可用的声音列表
    async function loadVoices() {
        try {
            const response = await fetch('/api/speakers');
            const data = await response.json();
            
            if (data.success && data.speakers.length > 0) {
                voiceSelect.innerHTML = data.speakers.map(speaker => 
                    `<option value="${speaker.id}">${speaker.name}</option>`
                ).join('');
            } else {
                voiceSelect.innerHTML = '<option value="default">No voices available</option>';
            }
        } catch (error) {
            console.error('Error loading voices:', error);
            voiceSelect.innerHTML = '<option value="default">Error loading voices</option>';
        }
    }

    // 生成语音
    async function generateSpeech() {
        if (!textInput.value.trim()) {
            alert('Please enter some text');
            return;
        }

        // 更新UI状态
        generateBtn.disabled = true;
        generateBtn.classList.add('loading');
        statusDiv.textContent = 'Generating speech...';
        statusDiv.classList.add('animate-pulse');

        try {
            // 创建 FormData
            const formData = new URLSearchParams();
            formData.append('text', textInput.value);
            formData.append('speaker_id', voiceSelect.value);
            formData.append('language_id', 'en');

            const response = await fetch('/api/tts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData.toString()
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // 获取音频blob
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);

            // 更新音频播放器
            audioPlayer.src = audioUrl;
            audioContainer.classList.remove('hidden');
            audioPlayer.play();

            // 清理状态
            statusDiv.textContent = 'Generation complete!';
            setTimeout(() => {
                statusDiv.textContent = '';
            }, 3000);

        } catch (error) {
            console.error('Error generating speech:', error);
            statusDiv.textContent = 'Error generating speech';
            alert('Error generating speech. Please try again.');
        } finally {
            generateBtn.disabled = false;
            generateBtn.classList.remove('loading');
            statusDiv.classList.remove('animate-pulse');
        }
    }

    // 事件监听
    generateBtn.addEventListener('click', generateSpeech);
    textInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            generateSpeech();
        }
    });

    // 初始化加载声音列表
    loadVoices();
});

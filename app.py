from __future__ import annotations
import streamlit as st
from devsentinel.analyzer import analyze, redact, export_report
from devsentinel.knowledge import search_docs

st.set_page_config(page_title='DevSentinel AI', page_icon='🛠️', layout='wide')
st.title('🛠️ DevSentinel')
st.caption('Developer issue triage • Offline rules + screenshot/video OCR • No source code execution')
st.info('MVP: deterministic troubleshooting assistant. It is not yet a trained multimodal agent or generative AI model.')
with st.sidebar:
    st.header('Investigation settings')
    include_docs = st.toggle('Suggest local knowledge articles', value=True)
    st.markdown('**Privacy:** Analysis runs locally. Remove secrets before uploading. Uploaded data is not intentionally persisted by this app.')
    st.markdown('**Next:** add repo-aware search, Whisper audio, and an approved sandbox patch runner.')

log_tab, screenshot_tab, video_tab, example_tab = st.tabs(['📋 Paste logs / code', '🖼️ Screenshot OCR', '🎬 Screen recording', '🧪 Try an example'])
with log_tab:
    typed = st.text_area('Paste a traceback, terminal output, or error message', height=240, placeholder='Paste the relevant error…')
    log_file = st.file_uploader('Or upload a .txt / .log file', type=['txt','log'], key='log')
with screenshot_tab:
    picture = st.file_uploader('Upload a PNG/JPG screenshot (max 8 MB)', type=['png','jpg','jpeg'], key='screenshot')
    if picture:
        st.image(picture, caption='Your screenshot', width=520)
with video_tab:
    video_file = st.file_uploader('Upload a screen recording (MP4 / MOV / WEBM, max 30 MB, max 2 minutes)', type=['mp4','mov','webm'], key='video')
    frame_count = st.slider('Frames to inspect', min_value=2, max_value=8, value=6)
    if video_file:
        st.video(video_file)
with example_tab:
    example = st.checkbox('Use the sample PyArrow build error')
    if example:
        st.code('Python 3.14.2\nERROR: Failed building wheel for pyarrow\nCould not find a package configuration file provided by "Arrow"', language='text')

if st.button('🔎 Investigate', type='primary', use_container_width=True):
    combined = []
    if typed.strip():
        combined.append(typed)
    if log_file:
        if log_file.size > 1_000_000:
            st.error('Log file exceeds the 1 MB limit.')
            st.stop()
        combined.append(log_file.getvalue().decode('utf-8', errors='replace'))
    if picture:
        try:
            from devsentinel.ocr import extract_screenshot
            extracted = extract_screenshot(picture.getvalue())
            st.subheader('Extracted screenshot text')
            st.code(redact(extracted[:4000]), language='text')
            combined.append(extracted)
        except (ValueError, RuntimeError, OSError, TimeoutError) as exc:
            st.warning(f'Screenshot processing unavailable: {exc}')
    if video_file:
        try:
            if video_file.size > 30_000_000:
                raise ValueError('Video exceeds 30 MB.')
            from devsentinel.video import inspect_video
            sampled, evidence, video_text = inspect_video(video_file.getvalue(), frame_count=frame_count)
            st.subheader('Video timeline')
            st.caption(f'{sampled.duration:.1f}-second recording; {len(evidence)} frames inspected. OCR is approximate.')
            for frame, frame_text in evidence:
                with st.expander(f'Frame at {frame.seconds:.1f} seconds'):
                    st.image(frame.png, width=480)
                    st.code(frame_text or '[No readable text]', language='text')
            combined.append(video_text)
        except (RuntimeError, ValueError, OSError, TimeoutError) as exc:
            st.warning(f'Video processing unavailable: {exc}')
    if example:
        combined.append('Python 3.14.2\nERROR: Failed building wheel for pyarrow\nCould not find a package configuration file provided by "Arrow"')
    full_text = '\n'.join(combined)
    if not full_text.strip():
        st.warning('Add a log, screenshot, or sample error to investigate.')
        st.stop()
    findings = analyze(full_text)
    st.subheader('Investigation results')
    if not findings:
        st.warning('No known error signature found. Try uploading a complete traceback or clearer screenshot.')
    for item in findings:
        with st.expander(f'🔍 {item.title} — {item.category}', expanded=True):
            st.code(item.evidence, language='text')
            st.write(item.explanation)
            st.markdown('**Suggested checks**')
            for step in item.actions:
                st.write('• ' + step)
            st.caption(f'Rule priority: {item.score}/100 (not a model confidence probability)')
    if include_docs:
        matches = search_docs(full_text)
        if matches:
            st.subheader('Local knowledge snippets')
            for title, body in matches:
                st.markdown(f'**{title}** — {body}')
    st.download_button('⬇️ Download redacted report', data=export_report(findings, full_text), file_name='devsentinel_report.md', mime='text/markdown')

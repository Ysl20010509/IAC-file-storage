function download(fileId, filename) {
  fetch("/download", {
    method: "POST",
    body: JSON.stringify({ fileId: fileId, filename: filename }),
  }).then(response => response.blob())
  .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;  // Set desired filename here
      a.click();
  })
  .catch(error => {
      console.error('Download request failed:', error);
  });
}


document.getElementById('contact-form-el').addEventListener('submit', function(e) {
      e.preventDefault();
      document.getElementById('contact-form-el').style.display = 'none';
      document.getElementById('contact-success').style.display = 'block';
    });
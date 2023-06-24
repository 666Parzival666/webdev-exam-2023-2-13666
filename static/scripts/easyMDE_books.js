const easyMDE = new EasyMDE({
   element: document.getElementById('description'),
   lineWrapping: true,
   previewRender: function (plainText) {
     return plainText;
   }
});
const easyMDE = new EasyMDE({
   element: document.getElementById('comment'),
   lineWrapping: true,
   previewRender: function (plainText) {
     return plainText;
   }
});
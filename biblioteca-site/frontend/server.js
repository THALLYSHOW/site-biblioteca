const express = require("express");
const path = require("path");

const app = express();

const PORT = 3000;

// pasta pública
app.use(express.static(__dirname))

// rota principal
app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "index.html"));
});

// iniciar servidor
app.listen(PORT, () => {
  console.log(`Servidor rodando em http://localhost:${PORT}`);
});
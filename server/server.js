const express = require("express");
const morgan = require("morgan");
const fs = require("fs");
const path = require("path");
const argv = require("minimist")(process.argv.slice(2));

const app = express();

const port = argv.p || 3900;
const data_path = argv.d || path.join(__dirname, "..", "data/", "db.json");
// console.dir(port);
// console.dir(data_path);

app.use(express.static(path.join(__dirname, "..", "build")));

// create a write stream (in append mode)
var accessLogStream = fs.createWriteStream(path.join(__dirname, "access.log"), {
  flags: "a",
});

// setup the logger
app.use(morgan("combined", { stream: accessLogStream }));

app.get("*", (req, res) => {
  res.sendFile(path.join(__dirname, "..", "build", "index.html"));
});

app.listen(port);

const express = require("express");
const path = require("path");
const router = express.Router();

// Base path to landing pages (go two levels up from routes/common)
const basePath = path.join(__dirname, "..", "..","frontend", "public", "pages");

router.get("/", (req, res) => {
    res.sendFile(path.join(basePath, "index.html"));
});

module.exports = router;
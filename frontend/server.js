const express = require("express");
const path = require("path");
const app = express();
const PORT = 5500;
const os = require("os");

// ✅ Middleware to serve static files (CSS, JS, images)
app.use(express.static(path.join(__dirname, "public")));
app.use(express.json());

//######################## ROUTES #########################
const dashboardRoutes = require("./routes/index_routes");
app.use("/", dashboardRoutes);
// ###################### Test Route ######################
app.get("/ping", (req, res) => {
  res.json({ message: "Frontend Server is Running 🚀" });
});
// ###################### Start Server ######################

function getServerIP() {
  const nets = os.networkInterfaces();
  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      if (net.family === "IPv4" && !net.internal) return net.address;
    }
  }
  return "localhost";
}

const IP = getServerIP();

app.listen(PORT, "0.0.0.0", () => {
  console.log(`🌍 Open in browser: http://${IP}:${PORT}`);
});
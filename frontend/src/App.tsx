import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Stories from "./pages/Stories";
import Bugs from "./pages/Bugs";
import Scores from "./pages/Scores";

function App() {
  return (
    <BrowserRouter>
      <div style={{ fontFamily: "system-ui, sans-serif" }}>
        <nav
          style={{
            padding: "1rem 2rem",
            background: "#1a1a2e",
            color: "#fff",
            display: "flex",
            gap: "2rem",
            alignItems: "center",
          }}
        >
          <h1 style={{ margin: 0, fontSize: "1.5rem" }}>EQIP</h1>
          <Link to="/" style={{ color: "#e0e0e0", textDecoration: "none" }}>
            Dashboard
          </Link>
          <Link
            to="/stories"
            style={{ color: "#e0e0e0", textDecoration: "none" }}
          >
            Stories
          </Link>
          <Link to="/bugs" style={{ color: "#e0e0e0", textDecoration: "none" }}>
            Bugs
          </Link>
          <Link
            to="/scores"
            style={{ color: "#e0e0e0", textDecoration: "none" }}
          >
            Scores
          </Link>
        </nav>
        <main style={{ padding: "2rem" }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/stories" element={<Stories />} />
            <Route path="/bugs" element={<Bugs />} />
            <Route path="/scores" element={<Scores />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;

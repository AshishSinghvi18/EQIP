import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Stories from "./pages/Stories";
import Bugs from "./pages/Bugs";
import Scores from "./pages/Scores";
import StoryOnboarding from "./pages/StoryOnboarding";
import Leaderboard from "./pages/Leaderboard";
import Search from "./pages/Search";
import Coaching from "./pages/Coaching";
import Trends from "./pages/Trends";

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
            gap: "1.5rem",
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <h1 style={{ margin: 0, fontSize: "1.5rem" }}>EQIP</h1>
          <Link to="/" style={{ color: "#e0e0e0", textDecoration: "none" }}>
            Dashboard
          </Link>
          <Link
            to="/onboarding"
            style={{ color: "#e0e0e0", textDecoration: "none" }}
          >
            📥 Onboarding
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
          <Link
            to="/leaderboard"
            style={{ color: "#e0e0e0", textDecoration: "none" }}
          >
            🏆 Leaderboard
          </Link>
          <Link
            to="/coaching"
            style={{ color: "#e0e0e0", textDecoration: "none" }}
          >
            💡 Coaching
          </Link>
          <Link
            to="/search"
            style={{ color: "#e0e0e0", textDecoration: "none" }}
          >
            🔍 Search
          </Link>
          <Link
            to="/trends"
            style={{ color: "#e0e0e0", textDecoration: "none" }}
          >
            📈 Trends
          </Link>
        </nav>
        <main style={{ padding: "2rem" }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/onboarding" element={<StoryOnboarding />} />
            <Route path="/stories" element={<Stories />} />
            <Route path="/bugs" element={<Bugs />} />
            <Route path="/scores" element={<Scores />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route path="/coaching" element={<Coaching />} />
            <Route path="/trends" element={<Trends />} />
            <Route path="/search" element={<Search />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;

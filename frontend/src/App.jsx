import { Route, Routes } from "react-router-dom";
import { AppShell } from "./components.jsx";
import { Home } from "./pages/Home.jsx";
import { RecordDetail } from "./pages/RecordDetail.jsx";
import { Review } from "./pages/Review.jsx";
import { Upload } from "./pages/Upload.jsx";

function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/review" element={<Review />} />
        <Route path="/record/:id" element={<RecordDetail />} />
      </Routes>
    </AppShell>
  );
}

export default App;

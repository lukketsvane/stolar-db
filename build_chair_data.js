const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const noregDir = path.join(__dirname, 'noreg');
const publicNoregDir = path.join(__dirname, 'turnable-chair', 'public', 'noreg');
const chairsDataPath = path.join(__dirname, 'turnable-chair', 'public', 'data', 'chairs.json');

if (!fs.existsSync(publicNoregDir)) fs.mkdirSync(publicNoregDir, { recursive: true });
if (!fs.existsSync(path.dirname(chairsDataPath))) fs.mkdirSync(path.dirname(chairsDataPath), { recursive: true });

// Run the video cropping script first to ensure all videos are square 1x1
console.log("Ensuring all videos are square 1x1 aspect ratio...");
try {
    execSync('python crop_videos_to_square.py', { stdio: 'inherit' });
} catch (e) {
    console.error("Warning: Video cropping failed. Ensure python and opencv are installed.");
}

const chairs = [];

const joinSafe = (val) => {
    if (Array.isArray(val)) return val.join(", ");
    if (typeof val === 'string') return val;
    return String(val || "");
};

function cleanBguwFilename(dir, filename) {
    if (filename.includes('_bguw_bguw')) {
        let newName = filename.replace(/(_bguw)+/g, '_bguw');
        const oldPath = path.join(dir, filename);
        const newPath = path.join(dir, newName);
        if (fs.existsSync(newPath) && oldPath !== newPath) {
            fs.unlinkSync(oldPath);
        } else if (oldPath !== newPath) {
            fs.renameSync(oldPath, newPath);
        }
        return newName;
    }
    return filename;
}

if (fs.existsSync(noregDir)) {
  const folders = fs.readdirSync(noregDir);
  for (const folder of folders) {
    const folderPath = path.join(noregDir, folder);
    if (!fs.statSync(folderPath).isDirectory()) continue;

    let files = fs.readdirSync(folderPath);
    files = files.map(f => cleanBguwFilename(folderPath, f));

    let metaFile = files.find(f => f.endsWith('.json') && f.startsWith(folder));
    if (!metaFile) continue;

    let metaData = {};
    try {
        metaData = JSON.parse(fs.readFileSync(path.join(folderPath, metaFile), 'utf8'));
    } catch (e) {
        continue;
    }

    const prodStad = joinSafe(metaData["Produksjonssted"]).toLowerCase();
    const isNorwegian = prodStad.includes("norge") || prodStad.includes("norway");
    if (!isNorwegian) continue;

    let bguwImage = files.find(f => f.endsWith('_bguw.png'));
    if (!bguwImage) {
        // Skip entries that don't have a solid white background version yet
        continue;
    }

    let videoFile = files.find(f => f.endsWith('.mp4'));
    let fallbackImage = files.find(f => f.endsWith('.png') && !f.includes('_bguw'));
    let imageFile = bguwImage;

    const destFolder = path.join(publicNoregDir, folder);
    if (!fs.existsSync(destFolder)) fs.mkdirSync(destFolder, { recursive: true });

    if (videoFile) fs.copyFileSync(path.join(folderPath, videoFile), path.join(destFolder, videoFile));
    if (imageFile) fs.copyFileSync(path.join(folderPath, imageFile), path.join(destFolder, imageFile));
    if (fallbackImage) fs.copyFileSync(path.join(folderPath, fallbackImage), path.join(destFolder, fallbackImage));

    chairs.push({
      id: folder,
      symbol: folder.substring(0, 2),
      number: folder.split('.').pop() || folder,
      name: metaData.title || metaData.Betegnelse || folder,
      video: videoFile ? `/noreg/${folder}/${videoFile}` : "",
      thumbVideo: videoFile ? `/noreg/${folder}/${videoFile}` : "",
      thumb: imageFile ? `/noreg/${folder}/${imageFile}` : "",
      source: metaData.url || "",
      text: metaData.Beskrivelse || metaData["Materiale og teknikk"] || "",
      specs: metaData["Mål"] || "",
      producer: metaData.Produsent || "",
      year: metaData.Datering || "",
      materials: joinSafe(metaData.Materiale),
      techniques: joinSafe(metaData.Teknikk),
      classification: metaData.Klassifikasjon || "",
      inventoryNr: metaData["Inventarnr."] || "",
      acquisition: metaData.Ervervelse || "",
      photo: metaData.Foto || "",
      location: metaData["Produksjonssted"] || ""
    });
  }
}

fs.writeFileSync(chairsDataPath, JSON.stringify(chairs, null, 2));
console.log(`Generated data for ${chairs.length} Norwegian chairs. Videos are cropped to 1:1.`);

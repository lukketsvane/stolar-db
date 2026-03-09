import { put, list } from '@vercel/blob';
import fs from 'fs';
import path from 'path';

const BLOB_READ_WRITE_TOKEN = "vercel_blob_rw_nu146j3JmwmJgdvV_rJmcpU5sihy76eq2BCmfTWhfG5VegP";

async function syncToBlob() {
  const modelDir = path.join(process.cwd(), 'public', 'models');
  const imageDir = path.join(process.cwd(), 'public', 'bg-uniform white');
  
  const modelMap = {};
  const imageMap = {};

  // 1. Upload Models
  if (fs.existsSync(modelDir)) {
    const dirs = fs.readdirSync(modelDir, { withFileTypes: true }).filter(d => d.isDirectory());
    console.log(`Fann ${dirs.length} modell-mapper. Startar opplasting...`);
    
    for (const dir of dirs) {
      const dirPath = path.join(modelDir, dir.name);
      const glbFile = fs.readdirSync(dirPath).find(f => f.endsWith('.glb'));
      
      if (glbFile) {
        const filePath = path.join(dirPath, glbFile);
        const fileBuffer = fs.readFileSync(filePath);
        try {
          const blob = await put(`models/${dir.name}/${glbFile}`, fileBuffer, {
            access: 'public',
            token: BLOB_READ_WRITE_TOKEN,
            contentType: 'model/gltf-binary'
          });
          modelMap[dir.name] = blob.url;
          console.log(`[MODEL] Lasta opp: ${dir.name}`);
        } catch (err) {
          console.error(`Feil ved opplasting av modell ${dir.name}:`, err);
        }
      }
    }
  }

  // 2. Upload Images
  if (fs.existsSync(imageDir)) {
    const images = fs.readdirSync(imageDir).filter(f => f.endsWith('.png'));
    console.log(`Fann ${images.length} bilete. Startar opplasting...`);
    
    for (const img of images) {
      const id = img.split('_')[0].replace('.png', '');
      const filePath = path.join(imageDir, img);
      const fileBuffer = fs.readFileSync(filePath);
      
      try {
        const blob = await put(`images/${img}`, fileBuffer, {
          access: 'public',
          token: BLOB_READ_WRITE_TOKEN,
          contentType: 'image/png'
        });
        imageMap[id] = blob.url;
        console.log(`[IMAGE] Lasta opp: ${id}`);
      } catch (err) {
        console.error(`Feil ved opplasting av bilete ${img}:`, err);
      }
    }
  }

  // 3. Save Mappings
  const dataDir = path.join(process.cwd(), 'public', 'data');
  fs.writeFileSync(path.join(dataDir, 'model_map.json'), JSON.stringify(modelMap, null, 2));
  fs.writeFileSync(path.join(dataDir, 'image_map.json'), JSON.stringify(imageMap, null, 2));
  
  console.log("Synkronisering ferdig!");
}

syncToBlob();

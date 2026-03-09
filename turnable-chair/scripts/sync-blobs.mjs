import { list } from '@vercel/blob';
import fs from 'fs';
import path from 'path';

const BLOB_READ_WRITE_TOKEN = "vercel_blob_rw_nu146j3JmwmJgdvV_rJmcpU5sihy76eq2BCmfTWhfG5VegP";

async function updateMappings() {
  console.log("Hentar filer frå Vercel Blob...");
  
  try {
    const { blobs } = await list({
      token: BLOB_READ_WRITE_TOKEN,
    });

    const modelMap = {};
    const imageMap = {};

    blobs.forEach(blob => {
      const filename = blob.pathname.split('/').pop();
      const id = filename.split('_')[0].replace('.glb', '').replace('.png', '');

      if (filename.endsWith('.glb')) {
        modelMap[id] = blob.url;
      } else if (filename.endsWith('.png')) {
        // Only map if it's likely a chair image (starts with OK- or NMK.)
        if (id.startsWith('OK-') || id.startsWith('NMK.')) {
          imageMap[id] = blob.url;
        }
      }
    });

    // Write the new maps
    const dataDir = path.join(process.cwd(), 'public', 'data');
    if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });

    fs.writeFileSync(path.join(dataDir, 'model_map.json'), JSON.stringify(modelMap, null, 2));
    fs.writeFileSync(path.join(dataDir, 'image_map.json'), JSON.stringify(imageMap, null, 2));

    console.log(`Oppdatert mapping! Fann ${Object.keys(modelMap).length} modellar og ${Object.keys(imageMap).length} bilete.`);
  } catch (error) {
    console.error("Feil ved henting av blobs:", error);
  }
}

updateMappings();

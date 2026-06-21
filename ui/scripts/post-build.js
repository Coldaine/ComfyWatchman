/*
 * @Author: ai-business-hql qingli.hql@alibaba-inc.com
 * @Date: 2025-02-17 20:53:45
 * @LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
 * @LastEditTime: 2025-06-05 11:18:48
 * @FilePath: /comfyui_copilot/ui/scripts/post-build.js
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
import fs from 'fs';
import path from 'path';
import glob from 'glob';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// 获取 __dirname 的等效值
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 在 dist/copilot_web 目录下查找所有 JS 文件
const distDir = path.resolve(__dirname, '../../dist/copilot_web');
const files = glob.sync(`${distDir}/**/*.js`);

files.forEach(file => {
    console.log('start modify', file)
    let content = fs.readFileSync(file, 'utf-8');

    // 检查是否已经有 getImportPath 函数（function 或 const 形式）
//     if (!content.includes('getImportPath')) {
//         content = `function getImportPath(filename) {
//     const apiBase = window.comfyAPI?.api?.api?.api_base;
//     if (apiBase) {
//         // 有 API base 时，使用完整路径
//         return \`\${apiBase.substring(1)}/copilot_web/\${filename}\`;
//     } else {
//         // 没有 API base 时，使用相对路径（因为所有文件都在同一目录）
//         return \`./\${filename}\`;
//     }
// }
// ` + content;
//     }
    if (!content.includes('getImportPath')) {
        content = `function getImportPath(filename) {
            return \`./\${filename}\`;
        }
            ` + content;
    }

    if (content.includes('__vite__mapDeps')) {
        // 尝试两种不同的格式
        let depsMatch = content.match(/const __vite__mapDeps=\(.*?m\.f=\[(.*?)\]/);
        
        // 如果第一种格式不匹配，尝试第二种格式（用于 input.js）
        if (!depsMatch) {
            depsMatch = content.match(/const __vite__mapDeps=\(.*?m\.f\|\|\(m\.f=\[(.*?)\]\)\)\)/);
        }
        
        if (depsMatch && depsMatch[1]) {
            const originalDeps = depsMatch[1];
            
            // 如果文件中还没有路径转换逻辑，则添加
            if (!content.includes('.map(path =>')) {
                // 替换整个 __vite__mapDeps 函数，处理两种可能的格式
                content = content.replace(
                    /const __vite__mapDeps=\([^;]+\);/,
                    `const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=[${originalDeps}].map(path => {
                        const apiBase = window.comfyAPI?.api?.api?.api_base;
                        if (apiBase) {
                            // 有 API base 时，使用完整路径
                            return \`\${apiBase.substring(1)}/\${path}\`;
                        } else {        
                            // 没有 API base 时，使用相对路径
                            return \`./\${path}\`;
                        }
                    }))))=>i.map(i=>d[i]);`
                );
            }
            console.log(`Modified ${path.basename(file)} - __vite__mapDeps`);
        } else {
            console.log(`No deps pattern found in ${path.basename(file)}`);
        }
    } else {
        console.log(`No __vite__mapDeps found in ${path.basename(file)}`);
    }

    // 处理 import("filename") 形式的动态导入
    const dynamicImportPattern = /import\("([^"]+\.js)"\)/g;
    if (dynamicImportPattern.test(content)) {
        content = content.replace(dynamicImportPattern, (match, filename) => {
            // 只处理相对路径的导入
            if (filename.startsWith('./') || !filename.includes('/')) {
                const cleanFilename = filename.startsWith('./') ? filename.substring(2) : filename;
                return `import(getImportPath("${cleanFilename}"))`;
            }
            return match;
        });
    }

    fs.writeFileSync(file, content, 'utf-8');
    console.log(`Modified ${path.basename(file)}`);
});

// 不需要单独处理 input.js，因为它已经在上面的循环中被处理了 
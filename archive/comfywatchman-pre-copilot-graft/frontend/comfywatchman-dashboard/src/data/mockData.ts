import { Model, Workflow, ActivityLogItem } from '../types';

export const mockModels: Model[] = [
  {
    id: '1',
    name: 'Realistic Vision V6.0',
    filename: 'realisticVisionV60_v60B1VAE.safetensors',
    type: 'Checkpoint',
    size: '5.21 GB',
    sizeBytes: 5210000000,
    dateAdded: '2024-01-15',
    status: 'available',
    path: '/models/checkpoints/',
    metadata: {
      description: 'Photorealistic model with excellent detail and lighting',
      triggerWords: ['realistic', 'photo'],
      baseModel: 'SD 1.5',
      version: '6.0 B1'
    },
    previewImages: ['https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=400&h=400&fit=crop'],
    associatedWorkflows: ['1', '3'],
    rating: 5,
    usageCount: 47
  },
  {
    id: '2',
    name: 'Detail Tweaker LORA',
    filename: 'add_detail.safetensors',
    type: 'LORA',
    size: '143 MB',
    sizeBytes: 143000000,
    dateAdded: '2024-02-01',
    status: 'available',
    path: '/models/loras/',
    metadata: {
      description: 'Adds fine details to generated images',
      triggerWords: ['detailed', 'sharp'],
      baseModel: 'SD 1.5',
      version: '1.0'
    },
    previewImages: ['https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?w=400&h=400&fit=crop'],
    associatedWorkflows: ['1', '2', '5'],
    rating: 4,
    usageCount: 89
  },
  {
    id: '3',
    name: 'VAE FT MSE 840000',
    filename: 'vae-ft-mse-840000-ema-pruned.safetensors',
    type: 'VAE',
    size: '319 MB',
    sizeBytes: 319000000,
    dateAdded: '2024-01-20',
    status: 'available',
    path: '/models/vae/',
    metadata: {
      description: 'Standard VAE for better color accuracy',
      baseModel: 'SD 1.5'
    },
    associatedWorkflows: ['1', '2', '3', '4'],
    rating: 5,
    usageCount: 134
  },
  {
    id: '4',
    name: 'ControlNet Canny',
    filename: 'control_v11p_sd15_canny.pth',
    type: 'ControlNet',
    size: '1.45 GB',
    sizeBytes: 1450000000,
    dateAdded: '2024-02-10',
    status: 'missing',
    path: '/models/controlnet/',
    metadata: {
      description: 'Edge detection controlnet for precise composition control',
      baseModel: 'SD 1.5',
      version: '1.1'
    },
    associatedWorkflows: ['6', '8'],
    rating: 5,
    usageCount: 23
  },
  {
    id: '5',
    name: 'SDXL Base 1.0',
    filename: 'sd_xl_base_1.0.safetensors',
    type: 'Checkpoint',
    size: '6.94 GB',
    sizeBytes: 6940000000,
    dateAdded: '2024-03-01',
    status: 'available',
    path: '/models/checkpoints/',
    metadata: {
      description: 'Base SDXL model for high resolution generation',
      baseModel: 'SDXL',
      version: '1.0'
    },
    previewImages: ['https://images.unsplash.com/photo-1614850523459-c2f4c699c52e?w=400&h=400&fit=crop'],
    associatedWorkflows: ['7', '9'],
    rating: 5,
    usageCount: 156
  },
  {
    id: '6',
    name: 'CLIP Vision Model',
    filename: 'clip_vision_g.safetensors',
    type: 'CLIP',
    size: '3.69 GB',
    sizeBytes: 3690000000,
    dateAdded: '2024-02-15',
    status: 'available',
    path: '/models/clip_vision/',
    metadata: {
      description: 'CLIP model for image interrogation and guidance',
      version: 'ViT-L/14'
    },
    associatedWorkflows: ['4', '7'],
    rating: 4,
    usageCount: 67
  },
  {
    id: '7',
    name: 'Ultimate SD Upscaler',
    filename: 'RealESRGAN_x4plus.pth',
    type: 'Upscale',
    size: '64 MB',
    sizeBytes: 64000000,
    dateAdded: '2024-01-25',
    status: 'available',
    path: '/models/upscale/',
    metadata: {
      description: '4x upscaling model for enhancing image resolution',
      version: 'x4plus'
    },
    associatedWorkflows: ['3', '5', '10'],
    rating: 5,
    usageCount: 201
  },
  {
    id: '8',
    name: 'Anime Style LORA',
    filename: 'anime_style_v2.safetensors',
    type: 'LORA',
    size: '156 MB',
    sizeBytes: 156000000,
    dateAdded: '2024-03-10',
    status: 'missing',
    path: '/models/loras/',
    metadata: {
      description: 'Anime and manga style enhancement',
      triggerWords: ['anime', 'manga style'],
      baseModel: 'SD 1.5',
      version: '2.0'
    },
    associatedWorkflows: ['11'],
    rating: 4,
    usageCount: 12
  }
];

export const mockWorkflows: Workflow[] = [
  {
    id: '1',
    name: 'Basic Text to Image',
    description: 'Standard text-to-image workflow with basic sampling',
    filename: 'txt2img_basic.json',
    createdDate: '2024-01-10',
    lastRun: '2024-03-14',
    status: 'ready',
    requiredModels: [
      { modelId: '1', modelName: 'realisticVisionV60_v60B1VAE.safetensors', available: true },
      { modelId: '2', modelName: 'add_detail.safetensors', available: true },
      { modelId: '3', modelName: 'vae-ft-mse-840000-ema-pruned.safetensors', available: true }
    ],
    previewImage: 'https://images.unsplash.com/photo-1547891654-e66ed7ebb968?w=400&h=300&fit=crop',
    category: ['generation', 'basic'],
    rating: 5,
    usageCount: 234
  },
  {
    id: '2',
    name: 'High Resolution Fix',
    description: 'Two-pass generation with upscaling for better quality',
    filename: 'hires_fix.json',
    createdDate: '2024-01-15',
    lastRun: '2024-03-13',
    status: 'ready',
    requiredModels: [
      { modelId: '1', modelName: 'realisticVisionV60_v60B1VAE.safetensors', available: true },
      { modelId: '2', modelName: 'add_detail.safetensors', available: true },
      { modelId: '3', modelName: 'vae-ft-mse-840000-ema-pruned.safetensors', available: true },
      { modelId: '7', modelName: 'RealESRGAN_x4plus.pth', available: true }
    ],
    previewImage: 'https://images.unsplash.com/photo-1614729939124-032f034e4e9e?w=400&h=300&fit=crop',
    category: ['generation', 'upscale'],
    rating: 5,
    usageCount: 189
  },
  {
    id: '3',
    name: 'ControlNet Edge Detection',
    description: 'Use canny edge detection to guide image generation',
    filename: 'controlnet_canny.json',
    createdDate: '2024-02-05',
    status: 'missing-models',
    requiredModels: [
      { modelId: '1', modelName: 'realisticVisionV60_v60B1VAE.safetensors', available: true },
      { modelId: '3', modelName: 'vae-ft-mse-840000-ema-pruned.safetensors', available: true },
      { modelId: '4', modelName: 'control_v11p_sd15_canny.pth', available: false }
    ],
    previewImage: 'https://images.unsplash.com/photo-1618556450994-a6a128ef0d9d?w=400&h=300&fit=crop',
    category: ['generation', 'controlnet'],
    rating: 4,
    usageCount: 45
  },
  {
    id: '4',
    name: 'SDXL Advanced',
    description: 'SDXL workflow with refiner and enhanced prompting',
    filename: 'sdxl_advanced.json',
    createdDate: '2024-03-01',
    lastRun: '2024-03-12',
    status: 'ready',
    requiredModels: [
      { modelId: '5', modelName: 'sd_xl_base_1.0.safetensors', available: true },
      { modelId: '6', modelName: 'clip_vision_g.safetensors', available: true }
    ],
    previewImage: 'https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?w=400&h=300&fit=crop',
    category: ['generation', 'sdxl'],
    rating: 5,
    usageCount: 167
  },
  {
    id: '5',
    name: 'Image to Image with Upscale',
    description: 'Transform existing images with AI enhancement',
    filename: 'img2img_upscale.json',
    createdDate: '2024-02-20',
    status: 'missing-models',
    requiredModels: [
      { modelId: '1', modelName: 'realisticVisionV60_v60B1VAE.safetensors', available: true },
      { modelId: '2', modelName: 'add_detail.safetensors', available: true },
      { modelId: '7', modelName: 'RealESRGAN_x4plus.pth', available: true },
      { modelId: '8', modelName: 'anime_style_v2.safetensors', available: false }
    ],
    previewImage: 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=400&h=300&fit=crop',
    category: ['transformation', 'upscale'],
    rating: 4,
    usageCount: 78
  }
];

export const mockActivityLog: ActivityLogItem[] = [
  {
    id: '1',
    type: 'execution',
    message: 'Workflow "Basic Text to Image" completed successfully',
    timestamp: '2024-03-14T10:30:00Z'
  },
  {
    id: '2',
    type: 'download',
    message: 'Model "SDXL Base 1.0" downloaded (6.94 GB)',
    timestamp: '2024-03-14T09:15:00Z'
  },
  {
    id: '3',
    type: 'import',
    message: 'New workflow "SDXL Advanced" imported',
    timestamp: '2024-03-14T08:45:00Z'
  },
  {
    id: '4',
    type: 'error',
    message: 'Workflow "ControlNet Edge Detection" failed: Missing model control_v11p_sd15_canny.pth',
    timestamp: '2024-03-13T16:20:00Z'
  },
  {
    id: '5',
    type: 'execution',
    message: 'Workflow "High Resolution Fix" completed successfully',
    timestamp: '2024-03-13T14:10:00Z'
  }
];

// Generate additional models to reach 106 total
const modelTypes: Array<Model['type']> = ['Checkpoint', 'LORA', 'VAE', 'CLIP', 'UNET', 'ControlNet', 'Upscale', 'Other'];
const statuses: Array<Model['status']> = ['available', 'missing'];

for (let i = 9; i <= 106; i++) {
  const type = modelTypes[Math.floor(Math.random() * modelTypes.length)];
  const status = Math.random() > 0.42 ? 'available' : 'missing'; // ~42% missing to get 44 missing models

  mockModels.push({
    id: i.toString(),
    name: `${type} Model ${i}`,
    filename: `model_${i}.safetensors`,
    type,
    size: `${(Math.random() * 5 + 0.1).toFixed(2)} GB`,
    sizeBytes: Math.floor(Math.random() * 5000000000 + 100000000),
    dateAdded: `2024-0${Math.floor(Math.random() * 3) + 1}-${Math.floor(Math.random() * 28) + 1}`,
    status,
    path: `/models/${type.toLowerCase()}/`,
    metadata: {
      description: `${type} model for various use cases`,
      baseModel: Math.random() > 0.5 ? 'SD 1.5' : 'SDXL'
    },
    associatedWorkflows: [],
    rating: Math.floor(Math.random() * 3) + 3,
    usageCount: Math.floor(Math.random() * 200)
  });
}

// Generate additional workflows to reach 17 total
for (let i = 6; i <= 17; i++) {
  mockWorkflows.push({
    id: i.toString(),
    name: `Workflow ${i}`,
    description: `Custom workflow for specific use case ${i}`,
    filename: `workflow_${i}.json`,
    createdDate: `2024-0${Math.floor(Math.random() * 3) + 1}-${Math.floor(Math.random() * 28) + 1}`,
    status: Math.random() > 0.94 ? 'ready' : 'missing-models', // Most missing to get ~1 ready
    requiredModels: Array.from({ length: Math.floor(Math.random() * 4) + 2 }, (_, idx) => ({
      modelId: `${idx + 1}`,
      modelName: `model_${idx + 1}.safetensors`,
      available: Math.random() > 0.3
    })),
    category: [['generation', 'upscale', 'controlnet', 'transformation'][Math.floor(Math.random() * 4)]],
    rating: Math.floor(Math.random() * 3) + 3,
    usageCount: Math.floor(Math.random() * 150)
  });
}

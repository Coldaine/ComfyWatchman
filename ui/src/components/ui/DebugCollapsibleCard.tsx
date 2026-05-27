/*
 * @Author: ai-business-hql qingli.hql@alibaba-inc.com
 * @Date: 2025-07-30 16:30:22
 * @LastEditors: ai-business-hql qingli.hql@alibaba-inc.com
 * @LastEditTime: 2025-07-30 17:24:40
 * @FilePath: /comfyui_copilot/ui/src/components/ui/DebugCollapsibleCard.tsx
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import BeautifyCard from "./BeautifyCard";

interface IProps {
  title?: string | React.ReactNode;
  isWorkflowUpdate?: boolean;
  className?: string;
  children: React.ReactNode;
}

const DebugCollapsibleCard: React.FC<IProps> = (props) => {
  const { title = '', isWorkflowUpdate = false, className = '', children } = props;
  
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <BeautifyCard className={`rounded-lg `} borderClassName='rounded-lg'>
      <div className={`flex flex-col ${className} ${!isOpen ? 'max-h-[200px]' : ''}`}>
        <div className="flex justify-between items-center pb-2 border-b border-gray-100">
          <div>
          {
            typeof title === 'string' ? <h3 className="text-sm text-[#fff] font-medium">{title}</h3> : title
          }
          </div>
          <button
            onClick={() => {
              setIsOpen(!isOpen)
            }}
          >
            {
              isOpen ? <ChevronUp className='text-gray-700' /> : <ChevronDown className='text-gray-700' />
            }
          </button>
        </div>
        <div className="overflow-hidden flex-1">
        {
          children
        }
        </div>
      </div>
      {/* {
        !isOpen && <div className="absolute bottom-0 left-0 right-0 h-12 w-full z-5 bg-debug-collapsible-card-bg pointer-events-none" />
      } */}
    </BeautifyCard>
  )
}

export default DebugCollapsibleCard;
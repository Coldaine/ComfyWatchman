const ImageLoading = () => {
    return (
        <div className="absolute top-0 left-0 w-full h-full bg-black/80 flex items-center justify-center">
            <div className="aspect-square h-3/5 border-4 border-solid border-[#d1d5db] border-t-[#00D9FF] rounded-full loading-spin" />
        </div>
    );
};

export default ImageLoading;
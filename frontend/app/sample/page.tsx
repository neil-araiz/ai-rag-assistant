"use client";

import { useState, useEffect } from "react";
import { sampleApi } from "@/lib/ai";

interface SampleResponse {
    documents_count: number;
}

export default function sample() {
    const [sample, setSample] = useState<SampleResponse | null>(null);

    const getSample = async () => {
        const response = await sampleApi();

        if (response) {
            setSample(response);
            console.log(response);
        }
    };
    
    useEffect(() => {
        getSample();
    }, []);
    
    return (
        <div>
            <h1>Sample Page</h1>
            <p>Count: {sample?.documents_count}</p>
        </div>
    );
}